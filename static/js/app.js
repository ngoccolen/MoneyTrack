document.addEventListener('DOMContentLoaded', function() {
    // ======================================================
    // 1. LOGIC SIDEBAR TOGGLE (Giữ nguyên)
    // ======================================================
    const parent = document.getElementById('finance-parent');
    const submenu = document.getElementById('finance-submenu');
    
    if (parent && submenu) {
        function updateSubmenuHeight() {
            if (submenu.classList.contains('open')) {
                submenu.style.height = submenu.scrollHeight + "px";
            } else {
                submenu.style.height = "0";
            }
        }
        
        parent.addEventListener('click', function() {
            parent.classList.toggle('open');
            submenu.classList.toggle('open');
            updateSubmenuHeight();
        });
        
        updateSubmenuHeight();
    }
    
    // ======================================================
    // 2. LOGIC MODAL FORM (Thu Chi & Vay Nợ - Giữ nguyên)
    // ======================================================
    const modalIds = ['transaction-modal', 'debt-loan-modal'];
    
    modalIds.forEach(id => {
        const modal = document.getElementById(id);
        if (!modal) return;
        
        const openBtn = document.getElementById(`open-${id}`);
        const closeBtn = modal.querySelector('.modal-close');
        const cancelBtn = modal.querySelector('.btn-cancel');

        if (openBtn) openBtn.addEventListener('click', () => modal.style.display = 'flex');
        if (closeBtn) closeBtn.addEventListener('click', () => modal.style.display = 'none');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', (e) => {
                e.preventDefault();
                modal.style.display = 'none';
            });
        }
        modal.addEventListener('click', (e) => {
            if (e.target === modal) modal.style.display = 'none';
        });
    });
    
    // ======================================================
    // 3. LOGIC TOGGLE BUTTONS (Giữ nguyên)
    // ======================================================
    document.querySelectorAll('.toggle-group').forEach(group => {
        group.addEventListener('click', function(e) {
            if (e.target.classList.contains('toggle-btn')) {
                group.querySelectorAll('.toggle-btn').forEach(btn => btn.classList.remove('active'));
                e.target.classList.add('active');
                
                const input = group.querySelector('input[type="hidden"]');
                if (input) input.value = e.target.dataset.type;
            }
        });
    });

    // ======================================================
    // 4. LOGIC QUÉT HÓA ĐƠN AI (NÂNG CẤP HIỂN THỊ ẢNH)
    // ======================================================
    if (window.location.pathname === '/scan') {
        const video = document.getElementById('video');
        const canvas = document.getElementById('canvas');
        const photoPreview = document.getElementById('photo-preview'); // Ảnh xem trước
        const btnCapture = document.getElementById('btn-capture');
        const fileUpload = document.getElementById('file-upload');
        const scanOverlay = document.getElementById('scan-overlay'); // Hiệu ứng quét
        let localStream = null;

        // Kích hoạt Camera
        navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
            .then(stream => { 
                video.srcObject = stream; 
                localStream = stream;
            })
            .catch(err => {
                console.error(err);
                alert("Không thể mở camera. Vui lòng dùng chức năng Tải ảnh.");
            });

        // Hàm chính: Hiển thị ảnh lên web và gửi đi quét
        async function previewAndScan(fileBlob) {
            // 1. Hiển thị ảnh lên khung nhìn ngay lập tức
            const imageUrl = URL.createObjectURL(fileBlob);
            photoPreview.src = imageUrl;
            photoPreview.style.display = 'block'; // Hiện ảnh
            video.style.display = 'none';         // Ẩn video camera
            if (scanOverlay) scanOverlay.style.display = 'block'; // Chạy hiệu ứng quét

            // 2. Gửi file lên server Flask
            const formData = new FormData();
            formData.append('file', fileBlob, 'scan.jpg');
            
            btnCapture.innerText = "🌀 Đang phân tích...";
            btnCapture.disabled = true;

            try {
                const response = await fetch('/api/scan-receipt', { method: 'POST', body: formData });
                
                if (!response.ok) throw new Error("Máy chủ phản hồi lỗi.");
                
                const data = await response.json();

                // 3. Điền kết quả trích xuất vào Form
                if (!data.amount || data.amount === 0) {
                    alert("⚠️ Không tìm thấy số tiền rõ ràng. Vui lòng tự nhập tay.");
                } else {
                    document.getElementById('res-amount').value = data.amount;
                    document.getElementById('res-date').value = data.date;
                    document.getElementById('res-note').value = data.note;
                    alert("✅ Đã trích xuất thông tin thành công!");
                }
            } catch (err) {
                console.error(err);
                alert("❌ Lỗi xử lý ảnh.");
            } finally {
                btnCapture.innerText = "📸 Chụp & Quét tiếp";
                btnCapture.disabled = false;
                if (scanOverlay) scanOverlay.style.display = 'none'; // Tắt hiệu ứng quét
            }
        }

        // Sự kiện chụp ảnh từ Camera
        btnCapture.addEventListener('click', () => {
            // Hiệu ứng nháy hình
            video.style.opacity = 0.5;
            setTimeout(() => video.style.opacity = 1, 100);

            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            canvas.getContext('2d').drawImage(video, 0, 0);
            
            video.pause(); 
            canvas.toBlob((blob) => {
                previewAndScan(blob);
            }, 'image/jpeg');
        });

        // Sự kiện tải file ảnh từ máy tính
        fileUpload.addEventListener('change', (e) => {
            if (e.target.files[0]) {
                previewAndScan(e.target.files[0]);
            }
        });

        // Nhấn vào ảnh để quay lại chế độ Camera (Nếu muốn chụp lại)
        photoPreview.addEventListener('click', () => {
            photoPreview.style.display = 'none';
            video.style.display = 'block';
            video.play();
        });
    }
});

document.addEventListener('DOMContentLoaded', function() {
    const aiBtn = document.getElementById('ai-float-button');
    const aiWindow = document.getElementById('ai-chat-window');
    const closeChat = document.getElementById('close-chat');
    const sendBtn = document.getElementById('btn-ai-send');
    const chatInput = document.getElementById('ai-chat-input');
    const chatContent = document.getElementById('ai-chat-content');

    // Mở/Đóng chat
    if(aiBtn) aiBtn.addEventListener('click', () => aiWindow.classList.toggle('ai-chat-hidden'));
    if(closeChat) closeChat.addEventListener('click', () => aiWindow.classList.add('ai-chat-hidden'));

    // Gửi tin nhắn nhập liệu
    async function sendMessage() {
        const msg = chatInput.value.trim();
        if (!msg) return;

        // Hiển thị tin nhắn của bạn lên khung chat
        chatContent.innerHTML += `<div class="message user-msg">${msg}</div>`;
        chatInput.value = '';
        chatContent.scrollTop = chatContent.scrollHeight;

        try {
            const response = await fetch('/api/ai-chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ message: msg })
            });
            const data = await response.json();

            // Hiển thị câu trả lời của AI
            chatContent.innerHTML += `<div class="message ai-msg">${data.reply}</div>`;
            chatContent.scrollTop = chatContent.scrollHeight;
            
            // Nếu thành công và đang ở trang thu chi, reload sau 1.2 giây để cập nhật bảng
            if(data.status === "success" && window.location.pathname.includes('thu-chi')) {
                setTimeout(() => location.reload(), 1200);
            }
        } catch (e) {
            chatContent.innerHTML += `<div class="message ai-msg">Lỗi: Không kết nối được với máy chủ AI.</div>`;
        }
    }

    if(sendBtn) sendBtn.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (e) => { if(e.key === 'Enter') sendMessage(); });
});

