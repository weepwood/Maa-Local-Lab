use std::{
    fs,
    io::{BufRead, BufReader},
    path::{Path, PathBuf},
    process::{Child, Command, Stdio},
    sync::Mutex,
    thread,
    time::Duration,
};
#[cfg(windows)]
use std::os::windows::process::CommandExt;
use serde::{Deserialize, Serialize};
use tauri::{Emitter, Manager, State};

#[derive(Serialize, Deserialize)]
struct Task {
    id: String,
    name: String,
    description: String,
    mode: String,
    enabled: bool,
}

struct Running(Mutex<Option<Child>>);

fn app_data(app: &tauri::AppHandle) -> Result<PathBuf, String> {
    let dir = app.path().app_data_dir().map_err(|e| e.to_string())?;
    fs::create_dir_all(&dir).map_err(|e| e.to_string())?;
    Ok(dir)
}

fn task_file(app: &tauri::AppHandle) -> Result<PathBuf, String> {
    Ok(app_data(app)?.join("tasks.json"))
}

fn development_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .unwrap_or(Path::new(env!("CARGO_MANIFEST_DIR")))
        .to_path_buf()
}

fn bundled_resource(app: &tauri::AppHandle) -> Result<PathBuf, String> {
    let dir = app.path().resource_dir().map_err(|e| e.to_string())?;
    let resource = dir.join("resource");
    if resource.join("pipeline").join("main.json").is_file() {
        return Ok(resource);
    }
    #[cfg(debug_assertions)]
    {
        let source = development_root().join("resource");
        if source.join("pipeline").join("main.json").is_file() {
            return Ok(source);
        }
    }
    Err("未发现内置 Pipeline/OCR 资源。请使用完整发行版或执行资源准备脚本".into())
}

fn default_pipeline(app: &tauri::AppHandle) -> Result<PathBuf, String> {
    Ok(bundled_resource(app)?.join("pipeline").join("main.json"))
}

fn editable_pipeline(app: &tauri::AppHandle) -> Result<PathBuf, String> {
    let folder = app_data(app)?.join("pipeline");
    fs::create_dir_all(&folder).map_err(|e| e.to_string())?;
    let file = folder.join("main.json");
    if !file.exists() {
        fs::copy(default_pipeline(app)?, &file).map_err(|e| {
            format!("创建用户 Pipeline 失败: {e}")
        })?;
    }
    Ok(file)
}

#[tauri::command]
fn load_tasks(app: tauri::AppHandle) -> Result<Vec<Task>, String> {
    let path = task_file(&app)?;
    if !path.exists() {
        return Ok(vec![Task {
            id: "demo".into(),
            name: "Windows 视觉自动化实验".into(),
            description: "隔离 Tkinter 窗口：OCR 识别 → 点击 → 保存验证".into(),
            mode: "foreground".into(),
            enabled: true,
        }]);
    }
    serde_json::from_slice(&fs::read(path).map_err(|e| e.to_string())?)
        .map_err(|e| e.to_string())
}

#[tauri::command]
fn save_tasks(app: tauri::AppHandle, tasks: Vec<Task>) -> Result<(), String> {
    if tasks.len() > 500 || tasks.iter().any(|task| {
        task.name.len() > 150
            || task.id.len() > 100
            || !["foreground", "background"].contains(&task.mode.as_str())
    }) {
        return Err("任务配置无效".into());
    }
    let path = task_file(&app)?;
    let tmp = path.with_extension("tmp");
    fs::write(
        &tmp,
        serde_json::to_vec_pretty(&tasks).map_err(|e| e.to_string())?,
    ).map_err(|e| e.to_string())?;
    fs::rename(tmp, path).map_err(|e| e.to_string())
}

#[tauri::command]
fn read_pipeline(app: tauri::AppHandle) -> Result<String, String> {
    fs::read_to_string(editable_pipeline(&app)?).map_err(|e| e.to_string())
}

#[tauri::command]
fn save_pipeline(app: tauri::AppHandle, content: String) -> Result<(), String> {
    if content.len() > 1024 * 1024 {
        return Err("Pipeline 超过 1 MiB".into());
    }
    let parsed: serde_json::Value = serde_json::from_str(&content)
        .map_err(|e| format!("Pipeline JSON 格式错误: {e}"))?;
    if !parsed.is_object() {
        return Err("Pipeline 必须是 JSON 对象".into());
    }
    let path = editable_pipeline(&app)?;
    let tmp = path.with_extension("tmp");
    fs::write(&tmp, content).map_err(|e| e.to_string())?;
    fs::rename(tmp, path).map_err(|e| e.to_string())
}

fn hide_console(command: &mut Command) {
    #[cfg(windows)]
    {
        command.creation_flags(0x08000000); // CREATE_NO_WINDOW
    }
    #[cfg(not(windows))]
    let _ = command;
}

fn build_runner(app: &tauri::AppHandle) -> Result<Command, String> {
    let resource_dir = app.path().resource_dir().map_err(|e| e.to_string())?;
    let packaged = resource_dir.join("engine").join("maa-runner.exe");
    if packaged.is_file() {
        return Ok(Command::new(packaged));
    }
    #[cfg(debug_assertions)]
    {
        let source = development_root();
        let script = source.join("run_demo.py");
        if script.is_file() {
            let env_python = source.join(".venv").join("Scripts").join("python.exe");
            let python = if env_python.is_file() {
                env_python.into_os_string()
            } else {
                "python".into()
            };
            let mut command = Command::new(python);
            command.arg(script);
            return Ok(command);
        }
    }
    Err("未发现打包的 MaaFramework 执行器。请重新下载安装完整包".into())
}

// stdout / stderr 的 handle 类型不同，用泛型分别启动日志消费线程。
fn forward_output<R: std::io::Read + Send + 'static>(
    app: &tauri::AppHandle,
    stream: &'static str,
    source: Option<R>,
) {
    if let Some(pipe) = source {
        let handle = app.clone();
        thread::spawn(move || {
            for line in BufReader::new(pipe).lines().map_while(Result::ok) {
                handle.emit("task-log", serde_json::json!({
                    "stream": stream,
                    "message": line
                })).ok();
            }
        });
    }
}

#[tauri::command]
fn run_demo(
    app: tauri::AppHandle,
    state: State<Running>,
    mode: String,
    simulate_failure: bool,
) -> Result<(), String> {
    if !["foreground", "background"].contains(&mode.as_str()) {
        return Err("不支持此运行模式".into());
    }
    let mut running = state.0.lock().map_err(|e| e.to_string())?;
    if let Some(child) = running.as_mut() {
        if child.try_wait().map_err(|e| e.to_string())?.is_none() {
            return Err("已经有实验任务在运行".into());
        }
    }
    let mut cmd = build_runner(&app)?;
    let resource = bundled_resource(&app)?;
    let pipeline = editable_pipeline(&app)?;
    let data = app_data(&app)?;
    let reports = data.join("runs");
    fs::create_dir_all(&reports).map_err(|e| e.to_string())?;
    cmd.env("PYTHONUTF8", "1")
        .env("PYTHONIOENCODING", "utf-8");
    cmd.arg("--mode").arg(mode)
        .arg("--resource-root").arg(&resource)
        .arg("--pipeline-file").arg(pipeline)
        .arg("--runs-dir").arg(reports)
        .current_dir(&data)
        .stdout(Stdio::piped()).stderr(Stdio::piped());
    if simulate_failure {
        cmd.arg("--simulate-failure");
    }
    hide_console(&mut cmd);
    let mut child = cmd.spawn().map_err(|e| format!("执行器启动失败: {e}"))?;
    let stdout = child.stdout.take();
    let stderr = child.stderr.take();
    *running = Some(child);
    drop(running);

    app.emit("task-status", "running").ok();
    forward_output(&app, "stdout", stdout);
    forward_output(&app, "stderr", stderr);

    thread::spawn(move || loop {
        thread::sleep(Duration::from_millis(400));
        let state = app.state::<Running>();
        let mut guard = match state.0.lock() {
            Ok(value) => value,
            Err(_) => return,
        };
        let complete = match guard.as_mut() {
            Some(child) => match child.try_wait() {
                Ok(Some(status)) => Some(status.success()),
                Ok(None) => None,
                Err(_) => Some(false),
            },
            None => return,
        };
        if let Some(success) = complete {
            *guard = None;
            drop(guard);
            app.emit("task-status", if success { "success" } else { "failed" }).ok();
            return;
        }
    });
    Ok(())
}

#[tauri::command]
fn stop_demo(app: tauri::AppHandle, state: State<Running>) -> Result<(), String> {
    let mut guard = state.0.lock().map_err(|e| e.to_string())?;
    if let Some(mut child) = guard.take() {
        #[cfg(windows)]
        {
            // 同时结束冻结执行器及其 --demo-ui 子进程，防止遗留试验窗口。
            let mut kill_tree = Command::new("taskkill");
            kill_tree.args(["/PID", &child.id().to_string(), "/T", "/F"]);
            hide_console(&mut kill_tree);
            let _ = kill_tree.status();
        }
        let _ = child.kill();
        let _ = child.wait();
        app.emit("task-status", "stopped").ok();
    }
    Ok(())
}

#[tauri::command]
fn list_reports(app: tauri::AppHandle) -> Result<Vec<serde_json::Value>, String> {
    let path = app_data(&app)?.join("runs");
    if !path.exists() {
        return Ok(vec![]);
    }
    let mut files = fs::read_dir(path).map_err(|e| e.to_string())?
        .filter_map(Result::ok)
        .map(|entry| entry.path().join("report.json"))
        .filter(|p| p.is_file())
        .collect::<Vec<_>>();
    files.sort();
    files.reverse();
    Ok(files.into_iter().take(100)
        .filter_map(|file| fs::read_to_string(file).ok())
        .filter_map(|s| serde_json::from_str(&s).ok())
        .collect())
}

pub fn run() {
    tauri::Builder::default()
        .manage(Running(Mutex::new(None)))
        .invoke_handler(tauri::generate_handler![
            load_tasks,
            save_tasks,
            read_pipeline,
            save_pipeline,
            run_demo,
            stop_demo,
            list_reports,
        ])
        .run(tauri::generate_context!())
        .expect("无法启动 Maa Local Lab");
}
