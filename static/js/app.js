document.addEventListener('DOMContentLoaded', function() {
    // ======================================================
    // LOGIC SIDEBAR TOGGLE
    // ======================================================
    const parent = document.getElementById('finance-parent');
    const submenu = document.getElementById('finance-submenu');
    
    if (parent && submenu) {
        // Hàm cập nhật chiều cao cho submenu
        function updateSubmenuHeight() {
            if (submenu.classList.contains('open')) {
                // Đặt chiều cao dựa trên nội dung thực tế để CSS transition hoạt động
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
        
        // Đảm bảo chiều cao được đặt đúng khi trang load nếu nó đang mở
        updateSubmenuHeight();
    }
    
    // ======================================================
    // LOGIC MODAL FORM (Hàm Show/Hide)
    // ======================================================
    const modalIds = ['transaction-modal', 'debt-loan-modal'];
    
    modalIds.forEach(id => {
        const modal = document.getElementById(id);
        if (!modal) return;
        
        // Nút mở modal
        const openBtn = document.getElementById(`open-${id}`);
        // Nút đóng modal
        const closeBtn = modal.querySelector('.modal-close');
        // Nút Hủy (trong footer)
        const cancelBtn = modal.querySelector('.btn-cancel');

        if (openBtn) {
            openBtn.addEventListener('click', () => modal.style.display = 'flex');
        }
        if (closeBtn) {
            closeBtn.addEventListener('click', () => modal.style.display = 'none');
        }
        if (cancelBtn) {
            cancelBtn.addEventListener('click', (e) => {
                e.preventDefault();
                modal.style.display = 'none';
            });
        }
        // Đóng khi click ra ngoài overlay
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.style.display = 'none';
            }
        });
    });
    
    // ======================================================
    // LOGIC TOGGLE BUTTONS (Form)
    // ======================================================
    document.querySelectorAll('.toggle-group').forEach(group => {
        group.addEventListener('click', function(e) {
            if (e.target.classList.contains('toggle-btn')) {
                // Đảm bảo chỉ có 1 nút được active
                group.querySelectorAll('.toggle-btn').forEach(btn => {
                    btn.classList.remove('active');
                });
                e.target.classList.add('active');
            }
        });
    });
});