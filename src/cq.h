// the max number of TCP connections that can wait in the queue
#define CONNECTION_BACKLOG 512

// maximum size of a sequence number netstring
#define MAX_SEQ_NS_LEN 25

// the maximum size of a frame
#define MAX_FRAME_LENGTH 1500 

/**

Components of the maximum payload size are:

1) The maximum size of a sequence number netstring, which is 24, i.e.:

                     20:18446744073709551615,

2) The maximum size of the payload netstring formatting, which is 6:
           
                            1468:,
   
3) The maximum size of the frame netstring formatting, which is also 6   

 */

#define MAX_PAYLOAD_LENGTH MAX_FRAME_LENGTH - 36

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
  char read_buffer[MAX_PAYLOAD_LENGTH];
  char write_buffer[25]; // max size of netstrung sequence number
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
