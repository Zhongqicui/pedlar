//+------------------------------------------------------------------+
//|                                                       pedlar.mq5 |
//|                                                            nuric |
//|                                  https://github.com/nuric/pedlar |
//+------------------------------------------------------------------+
#property copyright "nuric"
#property link      "https://github.com/nuric/pedlar"
#property version   "1.00"
//--- includes
#include <libzmq.mqh>
//--- input parameters
input bool tofile=false;
input string endpoint="tcp://*:7000";
//--- global variables
long ctx=NULL;
long socket=NULL;
datetime lastbar_date=0;
int filehandle=NULL;
//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
  {
//---
// Make sure we are not running in other environments such as optimisation
   if(MQLInfoInteger(MQL_OPTIMIZATION))
     {
      Print("Cannot run server in optimisation mode...");
      return(INIT_FAILED);
     }
// Check if we are backtesting, we will write to file instead
   if(tofile)
     {
      string filename=StringFormat("backtest_%s.csv",Symbol());
      Print("Saving ticks to file: ",filename);
      filehandle=FileOpen(filename,FILE_WRITE|FILE_CSV,',');
      if(filehandle==INVALID_HANDLE)
        {
         Print("Could not open file.");
         return(INIT_FAILED);
        }
      return(INIT_SUCCEEDED);
     }
// Check if DLL is allowed, otherwise we're doomed.
   if(!TerminalInfoInteger(TERMINAL_DLLS_ALLOWED))
     {
      Print("DLL imports are not allowed...");
      return(INIT_FAILED);
     }
// Create the ZMQ context that wraps sockets
   ctx=zmq_ctx_new();
   if(ctx==NULL)
     {
      Print("Failed to create context: ",zmq_errno());
      return(INIT_FAILED);
     }
   Print("Created new context:",ctx);
// Create the socket
   socket=zmq_socket(ctx,ZMQ_PUB);
   if(socket==NULL)
     {
      Print("Failed to create socket: ",zmq_errno());
      return(INIT_FAILED);
     }
// Set socket timeout (linger) time in milliseconds
   int lingertime[1]={4000};
   if(zmq_setsockopt(socket,ZMQ_LINGER,lingertime,sizeof(lingertime)))
     {
      Print("Failed to set socket options: ",zmq_errno());
      return(INIT_FAILED);
     }
// Bind the socket, note string is unicode (2 bytes)
// need to convert to char array first (1 byte)
   uchar ep[];
   StringToCharArray(endpoint,ep);
   if(zmq_bind(socket,ep))
     {
      Print("Failed to bind socket: ",zmq_errno());
      return(INIT_FAILED);
     }
// Set the initial bar time to detect new bars
   lastbar_date=(datetime)SeriesInfoInteger(Symbol(),Period(),SERIES_LASTBAR_DATE);
//---
   return(INIT_SUCCEEDED);
  }
//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
  {
//---
// Check writing to file option and close file
   if(tofile && filehandle!=NULL)
     {
      FileClose(filehandle);
      return;
     }
// Clean up socket and context
   if(zmq_close(socket))
     {
      Print("Failed to close socket:",zmq_errno());
     }
   if(zmq_ctx_term(ctx))
     {
      Print("Failed to terminate context: ",zmq_errno());
     }
   Print(MQLInfoString(MQL_PROGRAM_NAME)," deinitialised.");
  }
//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
  {
//---
// Publish tick data
   MqlTick last_tick;
   if(SymbolInfoTick(Symbol(),last_tick))
     {
      if(tofile)
         FileWrite(filehandle,"tick",last_tick.bid,last_tick.ask);
      else
        {
         tickbuf buf;
         buf.topic=0; // Tick data is topic 0
         buf.bid = last_tick.bid;
         buf.ask = last_tick.ask;
         int sent=zmq_send(socket,buf,sizeof(buf),NULL);
         if(sent!=sizeof(buf)) Print("Tick buffer send size did not match.");
        }
     }
   else Print("SymbolInfoTick() failed, error = ",GetLastError());

// Check and publish bar data
   datetime current_bardate=(datetime)SeriesInfoInteger(Symbol(),Period(),SERIES_LASTBAR_DATE);
   if(current_bardate>lastbar_date)
     {
      lastbar_date=current_bardate;
      barbuf buf;
      buf.topic=1; // Bar data is topic 1
      buf.open=iOpen(Symbol(),Period(),1); // Take last bar, shift=1
      buf.high=iHigh(Symbol(), Period(), 1);
      buf.low=iLow(Symbol(),Period(),1);
      buf.close=iClose(Symbol(),Period(),1);
      if(tofile)
         FileWrite(filehandle,"bar",buf.open,buf.high,buf.low,buf.close);
      else
        {
         int sent=zmq_send(socket, buf, sizeof(buf), NULL);
         if(sent!=sizeof(buf)) Print("Bar buffer send size did not match.");
         //Print("Bar:",buf.open,buf.high,buf.low,buf.close);
        }
     }
  }
//+------------------------------------------------------------------+
