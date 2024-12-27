// feature test macro for getaddrinfo() from man pages
#define _POSIX_C_SOURCE 200112L

#include <errno.h>
#include <netdb.h>      // for getaddrinfo()
#include <poll.h>       // for poll()
#include <signal.h>     // for signal()
#include <stdbool.h>    // for true/false, duh
#include <stddef.h>     // for size_t
#include <stdio.h>      // for printf(), perror(), fprintf(), puts()
#include <stdlib.h>     // for EXIT_SUCCESS, EXIT_FAILURE, atexit(), exit()
#include <string.h>     // for memcpy(), strncat(), strlen()
#include <sys/socket.h> // for socket(), bind(), listen(), accept(), recv(), send()
#include <unistd.h>     // for close()

#include "./vector.h"

// the size of byte prefixes
#define PREFIX_LENGTH sizeof(int)

// the max number of connections that can wait in the queue
#define CONNECTION_BACKLOG 128

// the maximum size of a message
#define MESSAGE_LENGTH 1024

// the maximum size of a message (including prefix)
#define BUFFER_LENGTH (PREFIX_LENGTH + MESSAGE_LENGTH)

enum ConnectionState {
  CONN_STATE_REQ = 0,
  CONN_STATE_RES,
  CONN_STATE_END,
};

struct Connection {
  int fd;
  enum ConnectionState state;
  char read_buffer[MESSAGE_LENGTH];
  char write_buffer[BUFFER_LENGTH];
};
typedef struct Connection Connection;

struct SequencedMessage {
  long sequence_number;
  char message_bytes[MESSAGE_LENGTH];
};
typedef struct SequencedMessage SequencedMessage;

SequencedMessage output_message;

static bool accept_new_connection(void);
static void handle_connection_io(Connection *conn);

static void cleanup(void);
static void handle_sigint(int sig);

// to store the address information of the server
struct addrinfo *server_info = NULL;

// the socket file descriptor
int socket_fd = -1;

// the sequence number
long sequence_num = 0;

// temp storage of sequence number as string
char sequence_chars[20];

// a vector of Connection structs to store the active connections
struct Vector *connections;

// a vector of pollfd structs to store the file descriptors that we want to
// poll for events
struct Vector *poll_fds = NULL;

int main(int argc, char *argv[]) {

  atexit(cleanup);
  signal(SIGPIPE, SIG_IGN);
  signal(SIGINT, handle_sigint);

  char* listen_port = argv[1];
  //  char* send_group = argv[2]; // e.g. 239.255.255.250 for SSDP
  //int send_port = atoi(argv[3]); // 0 if error, which is an invalid port
  
  // to store the return value of various function calls for error checking
  int rv;

  struct addrinfo hints = {0};     // make sure the struct is empty
  hints.ai_family = AF_UNSPEC;     // don't care whether it's IPv4 or IPv6
  hints.ai_socktype = SOCK_STREAM; // TCP stream sockets
  hints.ai_flags = AI_PASSIVE;     // fill in my IP for me

  // NULL to assign the address of my local host to socket structures
  rv = getaddrinfo(NULL, listen_port, &hints, &server_info);
  if (rv != 0) {
    fprintf(stderr, "getaddrinfo(): %s\n", gai_strerror(rv));
    return EXIT_FAILURE;
  }

  // loop through all the results and bind to the first we can
  struct addrinfo *p;
  for (p = server_info; p != NULL; p = p->ai_next) {
    // create a socket, which apparently is no good by itself because it's not
    // bound to an address and port number
    socket_fd = socket(p->ai_family, p->ai_socktype, p->ai_protocol);
    if (socket_fd == -1) {
      perror("socket()");
      continue;
    }

    // lose the "Address already in use" error message. why this happens
    // in the first place? well even after the server is closed, the port
    // will still be hanging around for a while, and if you try to restart
    // the server, you'll get an "Address already in use" error message
    int yes = 1;
    rv = setsockopt(socket_fd, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof yes);
    if (rv == -1) {
      perror("setsockopt()");
      exit(EXIT_FAILURE);
    }

    // bind the socket to the address and port number
    rv = bind(socket_fd, p->ai_addr, p->ai_addrlen);
    if (rv == -1) {
      close(socket_fd);
      perror("bind()");
      continue;
    }

    // binding was successful, so break out of the loop
    break;
  }

  // check if we were able to bind to an address and port number
  if (p == NULL) {
    fprintf(stderr, "failed to bind\n");
    exit(EXIT_FAILURE);
  }

  // TODO: join multicast group and maintain connection for outbound
  //       sequenced message output
  
  // free server_info because we don't need it anymore
  freeaddrinfo(server_info);
  server_info = NULL; // to avoid dangling pointer (& double free at cleanup())

  // time to listen for incoming connections
  // BACKLOG is the max number of connections that can wait in the queue
  rv = listen(socket_fd, CONNECTION_BACKLOG);
  if (rv == -1) {
    perror("listen()");
    return EXIT_FAILURE;
  }

  printf("Listening on port %s...\n", listen_port);
  printf("Current sequence number is %ld\n", sequence_num);

  // initialize connections vector
  connections = vector_init(sizeof(Connection), 0);

  // initialize the poll_fds vector
  poll_fds = vector_init(sizeof(struct pollfd), 0);

  // the event loop
  while (true) {
    // clear the poll_fds vector
    vector_clear(poll_fds);

    // initialize the pollfd struct for the socket file descriptor
    struct pollfd socket_pfd = {socket_fd, POLLIN, 0};
    vector_push(poll_fds, &socket_pfd);

    size_t num_connections = vector_length(connections);
    for (size_t i = 0; i < num_connections;) {
      Connection *conn = vector_get(connections, i);
      if (conn->state == CONN_STATE_END) {
        // if the connection is in the end state, close the connection
        close(conn->fd);

        // replace the current connection with the last connection in the vector
        if (i != num_connections - 1) {
          vector_set(connections, i,
                     vector_get(connections, num_connections - 1));
        }

        // remove the last connection from the vector
        vector_pop(connections);

        // decrement the number of connections
        --num_connections;

        continue;
      }

      // create pollfd struct and push it to the poll_fds vector
      struct pollfd pfd = {
          .fd = conn->fd,
          .events = (conn->state == CONN_STATE_REQ) ? POLLIN : POLLOUT,
          .revents = 0,
      };
      pfd.events = pfd.events | POLLERR;
      vector_push(poll_fds, &pfd);

      ++i;
    }

    // poll for active fds
    rv = poll(vector_data(poll_fds), vector_length(poll_fds), -1);
    if (rv == -1) {
      perror("poll()");
    }

    // process active connections
    size_t num_poll_fds = vector_length(poll_fds);
    for (size_t i = 1; i < num_poll_fds; ++i) {
      // skipped the first pollfd because it's the socket file descriptor

      struct pollfd *pfd = vector_get(poll_fds, i);
      if (pfd->revents) {
        Connection *conn = vector_get(connections, i - 1);

        if (conn == NULL) {
          // this should never happen, but just in case
          continue;
        }

        handle_connection_io(conn);
      }
    }

    // try to accept a new connection if the listening fd is active
    if (((struct pollfd *)vector_get(poll_fds, 0))->revents & POLLIN) {
      accept_new_connection();
    }
  }

  return EXIT_SUCCESS;
}
/**
static int is_connected(int sockfd) {
    char dummy;
    int result = recv(sockfd, &dummy, 1, MSG_PEEK);
    if (result == 0) {
        // Connection closed by the peer
        return 0;
    } else if (result == -1 && (errno == EAGAIN || errno == EWOULDBLOCK)) {
        // No data available, but the socket is still connected
        return 1;
    } else {
        // Error occurred
        return 0;
    }
}
*/
static bool accept_new_connection(void) {
  // accept
  struct sockaddr_storage client_addr = {};
  socklen_t addr_size = sizeof client_addr;

  int conn_fd = accept(socket_fd, (struct sockaddr *)&client_addr, &addr_size);
  if (conn_fd == -1) {
    perror("accept()");
    return false;
  }

  // creating the struct Conn
  Connection conn = {
      .fd = conn_fd,
      .state = CONN_STATE_REQ,
  };

  // add the connection to the connections vector
  vector_push(connections, &conn);

  printf("client %d connected\n", conn_fd);

  return true;
}

static void handle_connection_io(struct Connection *conn) {
  if (conn->state == CONN_STATE_REQ) {

    // TODO: handle length-prefixing here. Read n bytes (where n
    //       is the size of the prefix), then read the number of
    //       bytes indicated by casting the first n bytes to a
    //       long i. Then read i bytes into the buffer, prefix with
    //       sequence number, then prefix the combined byte array 
    //       with its own length and send to multicast connection
    int bytes_read =
        recv(conn->fd, conn->read_buffer, sizeof(conn->read_buffer) - 1, 0);
    if (bytes_read == -1) {
      perror("recv()");
      conn->state = CONN_STATE_END;
      return;
    } else if (bytes_read == 0) {
      printf("client %d disconnected\n", conn->fd);
      conn->state = CONN_STATE_END;
      return;
    }

    conn->read_buffer[bytes_read] = '\0';

   
    // TODO: add sequence number here to byte array containing the
    //       read buffer of the connection. Then send the buffer as
    //       a sequenced *and* length-prefixed byte array of the payload
    //       over the multicast interface specified on CLI.

    sequence_num++;
    output_message.sequence_number = sequence_num;
    memcpy(output_message.message_bytes, conn->read_buffer, sizeof(output_message.message_bytes));
    
    sprintf(sequence_chars, "%ld", sequence_num);

    memcpy(conn->write_buffer, sequence_chars, sizeof(sequence_chars));
    // this connection is ready to send a response now
    conn->state = CONN_STATE_RES;
   
    printf("%s: %s\n", sequence_chars, output_message.message_bytes);
  } else if (conn->state == CONN_STATE_RES) {

    //    if (is_connected(conn->fd) == 0) {
    int bytes_sent =
      // TODO: send to multicast
      send(conn->fd, conn->write_buffer, strlen(conn->write_buffer), 0);
    if (bytes_sent == -1) {
      perror("handle_client_message(): send()");
      conn->state = CONN_STATE_END;
      return;
    }
    conn->state = CONN_STATE_REQ;
  } else {
    fputs("handle_connection_io(): invalid state\n", stderr);
    exit(EXIT_FAILURE);
  }
}

static void cleanup(void) {
  // close the socket file descriptor
  if (socket_fd != -1) {
    close(socket_fd);
  }

  // free the addrinfo linked list
  if (server_info != NULL) {
    freeaddrinfo(server_info);
  }

  // free the connections vector
  if (connections != NULL) {
    vector_free(connections);
  }

  // free the poll_fds vector
  if (poll_fds != NULL) {
    vector_free(poll_fds);
  }
}

static void handle_sigint(int sig) {
  // call exit manually because atexit() registered the cleanup function
  exit(EXIT_SUCCESS);
}
