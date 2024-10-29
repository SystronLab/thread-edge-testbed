// 32-byte packet
#include <cstdint>
typedef struct _packetData {
uint16_t deviceId; // also used for Network-wide command identifier
uint16_t deviceFunctions; // also used as network command
uint16_t packetCount;
uint8_t deviceType; // also used in messages
uint8_t datatLen; // bytes
uint8_t data[24]; // also used in messages
} packetData;

/*****************************************************************************/
char *testbedLogTxString(uint32_t t, packetData* p)
{
    static uint8_t buf[sizeof(packetData)+TESTBEDLOG_HDRSIZE];
    buf[0] = TESTBEDLOG_TX_FMT;
    buf[1] = devState;
    memcpy(&buf[2], &t, 4);
    memcpy(&buf[6], p, sizeof(packetData));
    return (char *)buf;
}


/*****************************************************************************/
char *testbedLogRxString(uint32_t t, packetData* p)
{
    static uint8_t buf[sizeof(packetData)+TESTBEDLOG_HDRSIZE];
    buf[0] = TESTBEDLOG_RX_FMT;
    buf[1] = devState;
    memcpy(&buf[2], &t, 4);
    memcpy(&buf[6], p, sizeof(packetData));
    return (char *)buf;
}

/*****************************************************************************/
/*
Message Log Format;
[0]   : Log Type Identifier 'M'
[1]   : Device State
[5:2] : CPU time (in ms) since last cleared
[7:6] : Thread Short Address
[?:8] : Message string (NULL terminated)
*/
void testbedLogMsg(char* msg, int len)
{
    uint32_t t = k_uptime_get_32() - uptimeTickCount;
    otShortAddress sLA = otLinkGetShortAddress(openThreadInstance);
    char buf[len+8];
    buf[0] = TESTBEDLOG_MSG_FMT;
    buf[1] = devState;
    memcpy(&buf[2], &t, 4);
    memcpy(&buf[6], &sLA, 2);
    memcpy(&buf[8], msg, len);;
    testbedLogWrite(buf, len+8);
}


/*****************************************************************************/
char *testbedLogMsgTxString(uint32_t t, packetData* p)
{
    static uint8_t buf[sizeof(packetData)+TESTBEDLOG_HDRSIZE];
    buf[0] = TESTBEDLOG_MSG_FMT;
    buf[1] = 'T';
    memcpy(&buf[2], &t, 4);

    switch (p->deviceFunctions)
    {
        case TB_ENABLE_JAMMING_COUNTERMEASURE:
            memcpy(&buf[6], "COUNTER MEASURE ENABLED\0", sizeof("COUNTER MEASURE ENABLED\0"));
        break;
        case TB_DISABLE_JAMMING_COUNTERMEASURE:
            memcpy(&buf[6], "COUNTER MEASURE DISABLED\0", sizeof("COUNTER MEASURE DISABLED\0"));
        break;
        case TB_CHANNEL_HOP_ARRAY_UPDATE:
            memcpy(&buf[6], "UPDATING CHANNEL HOP LIST\0", sizeof("UPDATING CHANNEL HOP LIST\0"));
        break;
        default:
            return "";
    }
    return (char *)buf;
}


/*****************************************************************************/
char *testbedLogMsgRxString(uint32_t t, packetData* p)
{
    static uint8_t buf[sizeof(packetData)+TESTBEDLOG_HDRSIZE];
    buf[0] = TESTBEDLOG_MSG_FMT;
    buf[1] = 'R';
    switch (p->deviceFunctions)
    {
        case TB_ENABLE_JAMMING_COUNTERMEASURE:
            memcpy(&buf[2], "COUNTER MEASURE ENABLED\0", sizeof("COUNTER MEASURE ENABLED\0"));
        break;
        case TB_DISABLE_JAMMING_COUNTERMEASURE:
            memcpy(&buf[2], "COUNTER MEASURE DISABLED\0", sizeof("COUNTER MEASURE DISABLED\0"));
        break;
        case TB_CHANNEL_HOP_ARRAY_UPDATE:
            memcpy(&buf[2], "UPDATING CHANNEL HOP LIST\0", sizeof("UPDATING CHANNEL HOP LIST\0"));
        break;
        default:
            return "";
    }
    return (char *)buf;
}