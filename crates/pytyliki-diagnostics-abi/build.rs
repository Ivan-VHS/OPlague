use std::env;

fn main() {
    let library_dir = env::var("PYTYLIKI_LIB_DIR")
        .expect("PYTYLIKI_LIB_DIR must point to the trusted Pytyliki build directory");

    println!("cargo:rustc-link-search=native={library_dir}");
    println!("cargo:rustc-link-lib=dylib=pytyliki_ffi");
    println!("cargo:rerun-if-env-changed=PYTYLIKI_LIB_DIR");
}
