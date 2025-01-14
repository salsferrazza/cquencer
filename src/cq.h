// the size of byte prefixes
#define PREFIX_LENGTH sizeof(int)

// the max number of connections that can wait in the queue
#define CONNECTION_BACKLOG 128

// the maximum size of a message
#define MESSAGE_LENGTH 1024

// the maximum size of a message (including prefix)
#define BUFFER_LENGTH (PREFIX_LENGTH + MESSAGE_LENGTH + sizeof(long))

enum ConnectionState {
  CONN_STATE_REQ = 0,
  CONN_STATE_RES,
  CONN_STATE_END,
};

typedef struct {
  int fd;
  enum ConnectionState state;
  char read_buffer[BUFFER_LENGTH];
  char write_buffer[BUFFER_LENGTH];
} Connection;

typedef unsigned char byte;
typedef struct addrinfo addrinfo;
typedef struct pollfd pollfd;
typedef struct sockaddr sockaddr;
typedef struct sockaddr_in sockaddr_in;
typedef struct sockaddr_storage sockaddr_storage;
typedef struct timespec timespec;
typedef struct Vector Vector;

static void pack_msg(byte* output_buffer, byte* input_buffer, int length);
static bool accept_new_connection(void);
static void handle_connection_io(Connection *conn, int udp_fd, sockaddr_in multicast_addr);

static void now(char* datestr);
static void cleanup(void);
static void handle_sigint(int sig);

// to store the address information of the server
addrinfo *server_info = NULL;
