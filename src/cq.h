// the size of byte prefixes
#define PREFIX_LENGTH sizeof(int)

// the max number of connections that can wait in the queue
#define CONNECTION_BACKLOG 512

// the maximum size of a message
#define MAX_MESSAGE_LENGTH 1440

// the maximum size of a message (including prefix)
#define BUFFER_LENGTH PREFIX_LENGTH + sizeof(long) + MAX_MESSAGE_LENGTH

enum ConnectionState {
  CONN_STATE_REQ = 0,
  CONN_STATE_RES,
  CONN_STATE_END,
};

typedef unsigned char byte;
typedef struct addrinfo addrinfo;
typedef struct pollfd pollfd;
typedef struct sockaddr sockaddr;
typedef struct sockaddr_in sockaddr_in;
typedef struct sockaddr_storage sockaddr_storage;
typedef struct timespec timespec;
typedef struct Vector Vector;

typedef struct {
  int fd;
  enum ConnectionState state;
  char read_buffer[BUFFER_LENGTH];
  char write_buffer[BUFFER_LENGTH];
} Connection;

static bool accept_new_connection(void);
static void handle_connection_io(Connection *conn);
static void now(char* datestr);
static int secs(void);
static void logfile_name(char* logname);
static void cleanup(void);
static void handle_sigint(int sig);
static void handle_sigusr1(int sig);
static void usage(void);
static float get_mps(void);

// to store the address information of the server
addrinfo *server_info = NULL;

// set at non-zero for cq to log messages to a local file in same directory
int LOGMSG = 0;
