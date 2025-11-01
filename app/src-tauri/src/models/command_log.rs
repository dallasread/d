use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CommandLog {
    pub command: String,
    pub tool: String,
    pub args: Vec<String>,
    pub output: String,
    pub exit_code: i32,
    pub duration: f64, // in milliseconds
    pub domain: Option<String>,
}

impl CommandLog {
    pub fn new(
        tool: String,
        args: Vec<String>,
        output: String,
        exit_code: i32,
        duration: f64,
        domain: Option<String>,
    ) -> Self {
        let command = format!("{} {}", tool, args.join(" "));
        Self {
            command,
            tool,
            args,
            output,
            exit_code,
            duration,
            domain,
        }
    }
}
