//+------------------------------------------------------------------+
//|                                                       pedlar.mq5 |
//|                                                            nuric |
//|                                  https://github.com/nuric/pedlar |
//+------------------------------------------------------------------+
#property copyright "nuric"
#property link      "https://github.com/nuric/pedlar"
#property version   "1.00"
#property script_show_inputs
//--- includes
#include <libzmq.mqh>
#include <Trade\Trade.mqh>
//--- input parameters
input string   endpoint="tcp://localhost:7100";
input long polltimeout=2000; // miliseconds
//+------------------------------------------------------------------+
//| Script program start function                                    |
//+------------------------------------------------------------------+
void OnStart()
  {
//--- server variables
   long ctx=NULL;
   long socket=NULL;
   CTrade trade;
//---
// Check if DLL is allowed, otherwise we're doomed.
   if(!TerminalInfoInteger(TERMINAL_DLLS_ALLOWED))
     {
      Print("DLL imports are not allowed...");
      return;
     }
// Create the ZMQ context that wraps sockets
   ctx=zmq_ctx_new();
   if(ctx==NULL)
     {
      Print("Failed to create context: ",zmq_errno());
      return;
     }
   Print("Created new context:",ctx);
// Create the socket
   socket=zmq_socket(ctx,ZMQ_REP);
   if(socket==NULL)
     {
      Print("Failed to create socket: ",zmq_errno());
      return;
     }
// Set socket timeout (linger) time in milliseconds
   int lingertime[1]={4000};
   if(zmq_setsockopt(socket,ZMQ_LINGER,lingertime,sizeof(lingertime)))
     {
      Print("Failed to set socket options: ",zmq_errno());
      return;
     }
// Bind the socket, note string is unicode (2 bytes)
// need to convert to char array first (1 byte)
   uchar ep[];
   StringToCharArray(endpoint,ep);
   if(zmq_bind(socket,ep))
     {
      Print("Failed to bind socket: ",zmq_errno());
      return;
     }
//--- MAIN LOOP
// Setup polling
   pollitem items[1];
   items[0].socket=socket;
   items[0].fd=0;
   items[0].events=ZMQ_POLLIN;
   items[0].revents=0;
   Print("Starting server loop...");
   while(!IsStopped())
     {
      // Check any messages
      int num_active=zmq_poll(items,1,polltimeout);
      Print("NUM ACTIVE:",num_active);
      if(num_active==0) continue;
      // Receive request
      requestbuf req;
      req.action=0;
      req.order_id=0;
      req.volume=0;
      int recved=zmq_recv(socket,req,sizeof(req),NULL);
      if(recved!=sizeof(req)) Print("Request buffer received size did not match.");
      // Handle request
      int res=1;
      switch(req.action)
        {
         case 1: // Close
            res=trade.PositionClose(req.order_id);
            break;
         case 2: // Buy
            res=trade.Buy(req.volume);
            break;
         case 3: // Sell
            res=trade.Sell(req.volume);
            break;
         default:
            break;
        }
      // Form response
      responsebuf resp;
      resp.retcode=res;
      resp.order_id=trade.ResultDeal();
      resp.price=trade.ResultPrice();
      // Send response
      int sent=zmq_send(socket,resp,sizeof(resp),NULL);
      if(sent!=sizeof(resp)) Print("Response buffer sent size did not match.");
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
   Print("Server stopped.");
  }
//+------------------------------------------------------------------+
