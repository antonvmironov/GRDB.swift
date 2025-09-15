#include "sqlite3.h"
extern int sqlite3_uuid_init(sqlite3*, char**, const sqlite3_api_routines*);
extern int sqlite3_vec_init(sqlite3*, char**, const sqlite3_api_routines*);

static void autoload_custom(void) {
    sqlite3_auto_extension((void*)sqlite3_uuid_init);
    sqlite3_auto_extension((void*)sqlite3_vec_init);
}