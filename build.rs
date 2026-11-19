fn main() {
    slint_build::compile("ui/app.slint")
        .expect("failed to compile the DuckDriver Core Slint interface");
}
