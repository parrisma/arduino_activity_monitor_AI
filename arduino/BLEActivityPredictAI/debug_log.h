#define DEBUG_LG
//#undef DEBUG_LG

#ifdef DEBUG_LG
#define DPRINT(...)    Serial.print(__VA_ARGS__)     //Debug Print as a macro
#define DPRINTLN(...)  Serial.println(__VA_ARGS__)   //Debug Println as a macro
#define DFLUSH(...) Serial.flush(__VA_ARGS__)
#else
#define DPRINT(...)     //if not debug just a blank line
#define DPRINTLN(...)
#define DFLUSH(...)
#endif
