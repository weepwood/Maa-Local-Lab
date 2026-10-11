import argparse,json,os,subprocess,sys,time,uuid
from pathlib import Path
from datetime import datetime
def main():
 p=argparse.ArgumentParser();p.add_argument("--mode",choices=["foreground","background"],default="foreground");p.add_argument("--simulate-failure",action="store_true");a=p.parse_args()
 if os.name!="nt":raise RuntimeError("仅支持 Windows GUI 试验")
 from maa.toolkit import Toolkit
 from maa.resource import Resource
 from maa.tasker import Tasker
 from maa.controller import Win32Controller,MaaWin32ScreencapMethodEnum,MaaWin32InputMethodEnum
 root=Path(__file__).resolve().parent;session=uuid.uuid4().hex[:10];folder=root/"runs"/(datetime.now().strftime("%Y%m%d-%H%M%S")+"-"+session);folder.mkdir(parents=True);proof=folder/"saved.json";report={"session_id":session,"mode":a.mode,"passed":False,"nodes":[]}
 cmd=[sys.executable,str(root/"demo_app.py"),"--session",session,"--result",str(proof)]
 if a.simulate_failure:cmd.append("--simulate-failure")
 proc=subprocess.Popen(cmd)
 try:
  Toolkit.init_option(str(folder),{"logging":True,"save_draw":True,"save_on_error":True})
  for _ in range(80):
   found=[w for w in Toolkit.find_desktop_windows() if w.window_name=="MAA LOCAL LAB - "+session]
   if found:break
   time.sleep(.25)
  else:raise RuntimeError("窗口未找到")
  w=found[0];print("连接窗口",w.window_name,flush=True)
  if a.mode=="foreground":
   import ctypes
   ctypes.windll.user32.ShowWindow(w.hwnd,9);ctypes.windll.user32.SetForegroundWindow(w.hwnd)
   cap=MaaWin32ScreencapMethodEnum.ScreenDC;inp=MaaWin32InputMethodEnum.Seize
  else:cap=MaaWin32ScreencapMethodEnum.Background;inp=MaaWin32InputMethodEnum.PostMessage
  c=Win32Controller(hWnd=w.hwnd,screencap_method=cap,mouse_method=inp,keyboard_method=inp)
  if not c.post_connection().wait().succeeded:raise RuntimeError("窗口连接失败")
  resource=Resource()
  if not resource.post_bundle(str(root/"resource")).wait().succeeded:raise RuntimeError("请先准备 OCR 模型")
  tasker=Tasker()
  if not tasker.bind(resource,c) or not tasker.inited:raise RuntimeError("Tasker 初始化失败")
  job=tasker.post_task("开始测试").wait();detail=job.get()
  if detail:report["nodes"]=[{"name":n.name,"completed":n.completed} for n in detail.nodes]
  report["passed"]=bool(job.succeeded and any(n["name"]=="确认保存成功" and n["completed"] for n in report["nodes"]) and proof.exists() and json.loads(proof.read_text(encoding="utf-8")).get("session_id")==session)
 except Exception as e:report["error"]=str(e);print("错误:",e,flush=True)
 finally:
  (folder/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
  if proc.poll() is None:proc.terminate()
  print("实验完成：",report["passed"],"报告目录：",folder,flush=True)
 return 0 if report["passed"] else 1
if __name__=="__main__":sys.exit(main())
