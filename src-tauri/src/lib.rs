use std::{fs,io::{BufRead,BufReader},process::{Child,Command,Stdio},sync::Mutex,thread,time::Duration};
use tauri::{Manager,Emitter,State};
use serde::{Serialize,Deserialize};
#[derive(Serialize,Deserialize)]
struct Task{id:String,name:String,description:String,mode:String,enabled:bool}
struct Running(Mutex<Option<Child>>);
fn task_file(app:&tauri::AppHandle)->Result<std::path::PathBuf,String>{let p=app.path().app_data_dir().map_err(|e|e.to_string())?;fs::create_dir_all(&p).map_err(|e|e.to_string())?;Ok(p.join("tasks.json"))}
#[tauri::command]
fn load_tasks(app:tauri::AppHandle)->Result<Vec<Task>,String>{let p=task_file(&app)?;if !p.exists(){return Ok(vec![Task{id:"demo".into(),name:"Windows 视觉自动化实验".into(),description:"隔离 Tkinter 窗口：OCR 识别 → 点击 → 保存验证".into(),mode:"foreground".into(),enabled:true}]);}serde_json::from_slice(&fs::read(p).map_err(|e|e.to_string())?).map_err(|e|e.to_string())}
#[tauri::command]
fn save_tasks(app:tauri::AppHandle,tasks:Vec<Task>)->Result<(),String>{if tasks.len()>500||tasks.iter().any(|t|t.name.len()>150||!["foreground","background"].contains(&t.mode.as_str())){return Err("任务配置无效".into())}let p=task_file(&app)?;let tmp=p.with_extension("tmp");fs::write(&tmp,serde_json::to_vec_pretty(&tasks).map_err(|e|e.to_string())?).map_err(|e|e.to_string())?;fs::rename(tmp,p).map_err(|e|e.to_string())}
#[tauri::command]
fn read_pipeline()->Result<String,String>{fs::read_to_string("resource/pipeline/main.json").map_err(|e|e.to_string())}
#[tauri::command]
fn save_pipeline(content:String)->Result<(),String>{let _:serde_json::Value=serde_json::from_str(&content).map_err(|e|e.to_string())?;fs::write("resource/pipeline/main.json",content).map_err(|e|e.to_string())}
#[tauri::command]
fn run_demo(app:tauri::AppHandle,state:State<Running>,mode:String,simulate_failure:bool)->Result<(),String>{
 if !["foreground","background"].contains(&mode.as_str()){return Err("模式无效".into())}
 let mut lock=state.0.lock().map_err(|e|e.to_string())?;
 if let Some(c)=lock.as_mut(){if c.try_wait().map_err(|e|e.to_string())?.is_none(){return Err("已有任务运行中".into())}}
 let script=std::env::current_dir().map_err(|e|e.to_string())?.join("run_demo.py");
 if !script.exists(){return Err("请在仓库根目录启动 Tauri".into())}
 let local=std::env::current_dir().map_err(|e|e.to_string())?.join(".venv/Scripts/python.exe");
 let python=if local.exists(){local.to_string_lossy().to_string()}else{"python".into()};
 let mut cmd=Command::new(python);cmd.arg(script).arg("--mode").arg(mode).stdout(Stdio::piped()).stderr(Stdio::piped());
 if simulate_failure{cmd.arg("--simulate-failure");}
 let mut child=cmd.spawn().map_err(|e|e.to_string())?;
 let out=child.stdout.take();let err=child.stderr.take();*lock=Some(child);drop(lock);
 app.emit("task-status","running").ok();
 for (stream,pipe) in [("stdout",out),("stderr",err)]{if let Some(p)=pipe{let a=app.clone();thread::spawn(move||for line in BufReader::new(p).lines().map_while(Result::ok){a.emit("task-log",serde_json::json!({"stream":stream,"message":line})).ok();});}}
 thread::spawn(move||loop{thread::sleep(Duration::from_millis(400));let s=app.state::<Running>();let mut l=match s.0.lock(){Ok(v)=>v,Err(_)=>return};let result=match l.as_mut(){Some(c)=>match c.try_wait(){Ok(Some(x))=>Some(x.success()),Ok(None)=>None,Err(_)=>Some(false)},None=>return};if let Some(success)=result{*l=None;drop(l);app.emit("task-status",if success{"success"}else{"failed"}).ok();return}});
 Ok(())
}
#[tauri::command]
fn stop_demo(app:tauri::AppHandle,state:State<Running>)->Result<(),String>{let mut l=state.0.lock().map_err(|e|e.to_string())?;if let Some(mut p)=l.take(){p.kill().map_err(|e|e.to_string())?;let _=p.wait();app.emit("task-status","stopped").ok()}Ok(())}
#[tauri::command]
fn list_reports()->Result<Vec<serde_json::Value>,String>{let p=std::path::Path::new("runs");if !p.exists(){return Ok(vec![])}let mut v=fs::read_dir(p).map_err(|e|e.to_string())?.filter_map(Result::ok).map(|x|x.path().join("report.json")).filter(|x|x.is_file()).collect::<Vec<_>>();v.sort();v.reverse();Ok(v.into_iter().take(100).filter_map(|p|fs::read_to_string(p).ok()).filter_map(|s|serde_json::from_str(&s).ok()).collect())}
pub fn run(){tauri::Builder::default().manage(Running(Mutex::new(None))).invoke_handler(tauri::generate_handler![load_tasks,save_tasks,read_pipeline,save_pipeline,run_demo,stop_demo,list_reports]).run(tauri::generate_context!()).expect("Tauri startup failed")}
