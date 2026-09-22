// Minimal HTTP/1.1 server on lwIP raw TCP: POST /open /close /grip /stop /estop /keepalive, GET /status.
#include "httpd.h"
#include "gripper.h"
#include "config.h"
#include "hcfg.h"
#include "pico/cyw43_arch.h"
#include "lwip/tcp.h"
#include "pico/stdlib.h"
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
static uint32_t now_ms(void){ return to_ms_since_boot(get_absolute_time()); }
static float json_num(const char *body,const char *key){ const char *p=strstr(body,key); if(!p) return 0; p=strchr(p,':'); return p? (float)atof(p+1):0; }
static void json_str(const char *body,const char *key,char *out,int n){ out[0]=0; const char *p=strstr(body,key); if(!p) return; p=strchr(p,':'); if(!p) return; p=strchr(p,'"'); if(!p) return; p++; int i=0; while(*p && *p!='"' && i<n-1) out[i++]=*p++; out[i]=0; }
static void reply(struct tcp_pcb *pcb,int code,const char *body){
  char h[256]; int n=snprintf(h,sizeof h,"HTTP/1.1 %d OK\r\nContent-Type: application/json\r\nContent-Length: %d\r\nConnection: close\r\n\r\n",code,(int)strlen(body));
  tcp_write(pcb,h,n,TCP_WRITE_FLAG_COPY); tcp_write(pcb,body,strlen(body),TCP_WRITE_FLAG_COPY); tcp_output(pcb);
}
static err_t on_recv(void *arg,struct tcp_pcb *pcb,struct pbuf *p,err_t err){
  if(!p){ tcp_close(pcb); return ERR_OK; }
  char req[600]; int n=p->tot_len<599?p->tot_len:599; pbuf_copy_partial(p,req,n,0); req[n]=0; tcp_recved(pcb,p->tot_len); pbuf_free(p);
  char method[8]={0}, path[64]={0}; sscanf(req,"%7s %63s",method,path);
  const char *body=strstr(req,"\r\n\r\n"); body=body?body+4:"";
  char out[200]="{\"ok\":true}";
  if(!strcmp(method,"POST")){
    // reply first, then act: the band measures latency to the 200, and a slow servo write must not delay it
    if(!strcmp(path,"/open")) { reply(pcb,200,out); gr_open(); }
    else if(!strcmp(path,"/close")) { reply(pcb,200,out); gr_close(json_num(body,"\"force\"")); }
    else if(!strcmp(path,"/grip")) { char nm[24]; json_str(body,"\"name\"",nm,sizeof nm); bool pv=strstr(body,"\"preview\":true")!=NULL; reply(pcb,200,out); gr_grip(nm,pv); }
    else if(!strcmp(path,"/stop")) { reply(pcb,200,out); gr_stop(); }
    else if(!strcmp(path,"/estop")) { reply(pcb,200,out); gr_estop(); }
    else if(!strcmp(path,"/keepalive")) { reply(pcb,200,out); gr_keepalive(now_ms()); }
    else reply(pcb,404,"{\"error\":\"no such endpoint\"}");
  } else if(!strcmp(method,"GET") && !strcmp(path,"/status")) { gr_status_json(out,sizeof out); reply(pcb,200,out); }
  else if(!strcmp(path,"/config")) {   // Factum only: header X-Factum-Key
    char k[80]; snprintf(k,sizeof k,"X-Factum-Key: %s",hc.factum_key);
    if(!strstr(req,k)) reply(pcb,401,"{\"error\":\"key\"}");
    else { static char cj[600]; if(!strcmp(method,"POST")) hcfg_merge(body); hcfg_json(cj,sizeof cj); reply(pcb,200,cj); }
  }
  else reply(pcb,404,"{}");
  tcp_close(pcb); return ERR_OK;
}
static err_t on_accept(void *arg,struct tcp_pcb *pcb,err_t err){ tcp_recv(pcb,on_recv); return ERR_OK; }
void httpd_start(void){ struct tcp_pcb *l=tcp_new(); tcp_bind(l,IP_ADDR_ANY,HTTP_PORT); l=tcp_listen(l); tcp_accept(l,on_accept); }
