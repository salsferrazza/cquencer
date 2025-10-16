//
// cq  - a central sequence number server that receives unsequenced
//       messages over TCP and sends sequenced UDP packets to 
//       the specified multicast address

// feature test macro for getaddrinfo() from man pages
#define _POSIX_C_SOURCE 200112L

#include <assert.h>
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
#include <time.h>       // for timespec, clock_gettime()
#include <unistd.h>     // for close()
#include <netinet/in.h>
#include <limits.h>
#include <arpa/inet.h>
#include "./vector.h"
#include "./cq.h"

// message log file pointer
FILE *logptr;

// strimg presentation of current PID
char pidstr[11];

// string timestamp of latest sequenced message
char curstamp[21];

// the tcp socket file descriptor
int tcp_fd = -1;

// the udp file descriptor
int udp_fd = -1;

// the sequence number
unsigned long sequence_num = 0;

// temporary storage of sequence number
// as a string for TCP client response
char sequence_chars[21]; // 20 is maximum size of unsigned long as string

// UDP output buffer
char udp_output_buffer[BUFFER_LENGTH];

//
int total_msg_len, payload_len, seq_len = 0;
char payload_ns[BUFFER_LENGTH];
char seq_ns[25];

// a vector of Connection structs to store the active connections
Vector *connections;
// std::vector<Connection> connections;

// a vector of pollfd structs to store the file descriptors that we want to
// poll for events
Vector *poll_fds = NULL;

int main(int argc, char *argv[]) {
   
  atexit(cleanup);
  signal(SIGPIPE, SIG_IGN);
  signal(SIGINT, handle_sigint);

  setbuf(stdout, NULL); // unbuffer STDOUT

  char* listen_port = argv[1];
  char* send_group = argv[2]; // e.g. 239.255.255.250 for SSDP
  int send_port = atoi(argv[3]); // 0 if error, which is an invalid port


  if (LOGMSG != 0) {
    // derive logfile name from PID and date, create descriptor for writing
    char logname[strlen(pidstr) + strlen("-") + strlen(curstamp) + strlen(".msg")];
    logfile_name((char *) logname);
    logptr = fopen(logname, "wb");
    if (logptr == NULL) {
      perror("fopen()");
      exit(EXIT_FAILURE);
    }
    setbuf(logptr, NULL); // unbuffer log file
  }
  
  // to store the return value of various function calls for error checking
  int rv;
  
  addrinfo hints = {0};     // make sure the struct is empty
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
  addrinfo *p = NULL;
  for (p = server_info; p != NULL; p = p->ai_next) {
    // create a socket, which apparently is no good by itself because it's not
    // bound to an address and port number
    tcp_fd = socket(p->ai_family, p->ai_socktype, p->ai_protocol);
    if (tcp_fd == -1) {
      perror("socket()");
      continue;
    }

    // lose the "Address already in use" error message. why this happens
    // in the first place? well even after the server is closed, the port
    // will still be hanging around for a while, and if you try to restart
    // the server, you'll get an "Address already in use" error message
    int yes = 1;
    rv = setsockopt(tcp_fd, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof yes);
    if (rv == -1) {
      perror("setsockopt()");
      exit(EXIT_FAILURE);
    }

    // bind the socket to the address and port number
    rv = bind(tcp_fd, p->ai_addr, p->ai_addrlen);
    if (rv == -1) {
      close(tcp_fd);
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

  // free server_info because we don't need it anymore
  freeaddrinfo(server_info);
  server_info = NULL; // to avoid dangling pointer (& double free at cleanup())

  // time to listen for incoming connections
  // BACKLOG is the max number of connections that can wait in the queue
  rv = listen(tcp_fd, CONNECTION_BACKLOG);
  if (rv == -1) {
    perror("listen()");
    return EXIT_FAILURE;
  }

  fprintf(stderr, "Listening on port %s...\n", listen_port);
  fprintf(stderr, "Current sequence number is %ld\n", sequence_num);
  
  // initialize connections vector
  connections = vector_init(sizeof(Connection), 0);

  // initialize the poll_fds vector
  poll_fds = vector_init(sizeof(pollfd), 0);

  /** SET UP MULTICAST FOR PUBLISHING **/
  
  sockaddr_in multicast_addr;
  memset(&multicast_addr, 0, sizeof(multicast_addr));
  multicast_addr.sin_family = AF_INET;
  multicast_addr.sin_addr.s_addr = inet_addr(send_group);
  multicast_addr.sin_port = htons(send_port);

  udp_fd = socket(multicast_addr.sin_family, SOCK_DGRAM, 0);
  if (udp_fd < 0) {
    perror("socket()");
    return 1;
  }
  
  // the event loop

  while (true) {
    // clear the poll_fds vector
    vector_clear(poll_fds);

    // initialize the pollfd struct for the socket file descriptor
    pollfd socket_pfd = {tcp_fd, POLLIN, 0};
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
      pollfd pfd = {
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

      pollfd *pfd = vector_get(poll_fds, i);
      if (pfd->revents) {
        Connection *conn = vector_get(connections, i - 1);

        if (conn == NULL) {
          // this should never happen, but just in case
          continue;
        }
        handle_connection_io(conn, udp_fd, multicast_addr);
      }
    }

    // try to accept a new connection if the listening fd is active
    if (((pollfd *)vector_get(poll_fds, 0))->revents & POLLIN) {
      accept_new_connection();
    }
  }
  return EXIT_SUCCESS;
}

static bool accept_new_connection(void) {
  // accept
  sockaddr_storage client_addr = {};
  socklen_t addr_size = sizeof client_addr;

  int conn_fd = accept(tcp_fd, (sockaddr *)&client_addr, &addr_size);
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

  return true;
}

static void handle_connection_io(Connection *conn, int udp_fd, sockaddr_in multicast_addr) {
  if (conn->state == CONN_STATE_REQ) {

    int bytes_read =
      recv(conn->fd, conn->read_buffer, sizeof(conn->read_buffer), 0);
    if (bytes_read == -1) {
      perror("recv()");
      conn->state = CONN_STATE_END;
      return;
    } else if (bytes_read == 0) {
      conn->state = CONN_STATE_END;
      return;
    }

    // terminate read buffer
    conn->read_buffer[bytes_read] = '\0';

    // increment sequence #
    // sequence_num++;   

    // save string representation of the sequence # 
    sprintf(sequence_chars, "%lu", ++sequence_num);
    
    // manufacture output message
    seq_len = strlen(sequence_chars);

    assert(seq_len > 0);    
    sprintf(seq_ns, "%d:%s,", seq_len, sequence_chars);

    total_msg_len += strlen(seq_ns);
    
    //    printf("%s\n", seq_ns);
    
    assert(strlen(seq_ns) > 0);
    
    payload_len = strlen(conn->read_buffer);
    sprintf(payload_ns, "%d:%s,", payload_len, conn->read_buffer);

    total_msg_len += strlen(payload_ns);
    
    printf("%d:%s%s,\n", total_msg_len, seq_ns, payload_ns);
    
    sprintf(udp_output_buffer, "%d:%s%s,", total_msg_len, seq_ns, payload_ns);

    if (LOGMSG) {
      // persist message locally    
      fprintf(logptr, "%s", udp_output_buffer);
    }
    
    // send output buffer over UDP
    int nbytes = sendto(
                        udp_fd,
                        udp_output_buffer,
                        strlen(udp_output_buffer),
                        0,
                        (sockaddr*) &multicast_addr,
                        sizeof(multicast_addr)
                        );
    if (nbytes < 0) {
      perror("sendto");
      return;
    }

    // populate TCP write buffer for client response
    memcpy(conn->write_buffer, sequence_chars, strlen(sequence_chars));

    // this connection is ready to send a response now
    conn->state = CONN_STATE_RES;

    // reset values for next iteration
    memset(udp_output_buffer, 0, BUFFER_LENGTH);
    memset(seq_ns, 0, strlen(seq_ns));
    memset(payload_ns, 0, strlen(payload_ns));
    total_msg_len = 0;
    seq_len = 0;
    payload_len = 0;
    
    
    // log
    // now((char *) curstamp);
    //    printf("%s send # %s: pay %d seq %d total %lu bytes\n",
    //     (char *) curstamp, sequence_chars, payload_len,
    //     seq_len, strlen(udp_output_buffer));
   
  } else if (conn->state == CONN_STATE_RES) {    
    int bytes_sent =
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

static void logfile_name(char *logname) {
  int pid = getpid();
  sprintf((char *) pidstr, "%d", pid);
  now((char *) curstamp);
  sprintf(logname, "%s-%s.msg", pidstr, curstamp);
}

static void now(char *datestr) {
  timespec tv;
  if (clock_gettime(CLOCK_REALTIME, &tv)) perror("error clock_gettime\n");
  int sec = tv.tv_sec;
  int nsec = tv.tv_nsec;
  sprintf(datestr, "%d%09d", sec, nsec);
}

static void cleanup(void) {
  // close the socket file descriptor
  if (tcp_fd != -1) {
    close(tcp_fd);
  }

  if (LOGMSG != 0) {
    // close the message log file descriptor
    if (logptr != NULL) {
      fclose(logptr);
    }
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
