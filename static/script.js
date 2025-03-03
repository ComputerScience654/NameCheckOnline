async function login() {
    let username = document.getElementById("loginUser").value;
    let password = document.getElementById("loginPass").value;

    let response = await fetch("http://127.0.0.1:5000/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
    });

    let data = await response.json();
    if (response.ok) {
        localStorage.setItem("token", data.token);
        alert("เข้าสู่ระบบสำเร็จ!");
        window.location.href = "/home";
    } else {
        alert("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง");
    }
}

document.getElementById("registerForm").addEventListener("submit", async function (event) {
    event.preventDefault(); // ป้องกันการโหลดหน้าใหม่

    let email = document.getElementById("regEmail").value;
    let username = document.getElementById("regUser").value;
    let password = document.getElementById("regPass").value;
    let confirmPassword = document.getElementById("confirmPass").value;

    if (password !== confirmPassword) {
        alert("รหัสผ่านไม่ตรงกัน");
        return;
    }

    let response = await fetch("http://127.0.0.1:5000/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, username, password })
    });

    let data = await response.json();
    if (response.ok) {
        alert("ลงทะเบียนสำเร็จ! กรุณาเข้าสู่ระบบ");
        window.location.href = "/login";
    } else {
        alert("เกิดข้อผิดพลาด: " + data.message);
    }
});

