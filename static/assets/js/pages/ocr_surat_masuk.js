    const suratMasukImageBaseUrl = "{{ url_for('ocr_surat_masuk.surat_masuk_image', id=0) }}";
    const staticImageBaseUrl = "{{ url_for('static', filename='ocr/surat_masuk/') }}";
    let currentIndex = 0;
    const extractedDataList = {{ extracted_data_list | tojson }};

    function openModal(index) {
        if (index < 0 || index >= extractedDataList.length) {
            alert("Indeks di luar batas.");
            return;
        }

        resetZoom();
        currentIndex = index;
        const data = extractedDataList[index];
        
        // Atur sumber gambar
        const imageSrc = data.id_suratMasuk !== null ? 
            suratMasukImageBaseUrl.replace('0', data.id_suratMasuk) : 
            staticImageBaseUrl + data.filename;
        document.getElementById('modal-image').src = imageSrc;

        // Isi nilai awal (hidden)
        document.getElementById('initial_full_letter_number').value = data.full_letter_number || '';
        document.getElementById('initial_pengirim_suratMasuk').value = data.pengirim_suratMasuk || '';
        document.getElementById('initial_penerima_suratMasuk').value = data.penerima_suratMasuk || '';
        document.getElementById('initial_isi_suratMasuk').value = data.isi_suratMasuk || '';

        // Isi form
        document.getElementById('filename').value = data.filename;
        document.getElementById('full_letter_number').value = data.full_letter_number || '';
        document.getElementById('pengirim_suratMasuk').value = data.pengirim_suratMasuk || '';
        document.getElementById('penerima_suratMasuk').value = data.penerima_suratMasuk || '';
        document.getElementById('kodesurat2').value = data.kodesurat2 || '';
        document.getElementById('jenis_surat').value = data.jenis_surat || '';
        document.getElementById('isi_suratMasuk').value = data.isi_suratMasuk || '';

        // Isi opsi tanggal
        const dateSelect = document.getElementById('selected_date');
        dateSelect.innerHTML = '<option value="">Pilih tanggal</option>';
        if (data.dates && data.dates.length > 0) {
            data.dates.forEach((date) => {
                const option = document.createElement('option');
                option.value = date;
                option.textContent = date;
                dateSelect.appendChild(option);
            });
            // Pilih tanggal pertama secara default
            dateSelect.options[1].selected = true;
        }

        $('#dataModal').modal('show');
    }

    function nextModal() {
        if (currentIndex < extractedDataList.length - 1) {
            openModal(currentIndex + 1);
        } else {
            alert("Tidak ada entri lagi untuk diproses.");
        }
    }

    function previousModal() {
        if (currentIndex > 0) {
            openModal(currentIndex - 1);
        } else {
            alert("Sudah di entri pertama.");
        }
    }

    function saveData() {
        const saveButton = document.getElementById('saveButton');
        const originalButtonText = saveButton.innerHTML;
        saveButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Menyimpan...';
        saveButton.disabled = true;

        const formData = {
            filename: document.getElementById('filename').value,
            initial_full_letter_number: document.getElementById('initial_full_letter_number').value,
            initial_pengirim_suratMasuk: document.getElementById('initial_pengirim_suratMasuk').value,
            initial_penerima_suratMasuk: document.getElementById('initial_penerima_suratMasuk').value,
            initial_isi_suratMasuk: document.getElementById('initial_isi_suratMasuk').value,
            full_letter_number: document.getElementById('full_letter_number').value.trim(),
            pengirim_suratMasuk: document.getElementById('pengirim_suratMasuk').value.trim(),
            penerima_suratMasuk: document.getElementById('penerima_suratMasuk').value.trim(),
            selected_date: document.getElementById('selected_date').value.trim(),
            kodesurat2: document.getElementById('kodesurat2').value.trim(),
            jenis_surat: document.getElementById('jenis_surat').value.trim(),
            isi_suratMasuk: document.getElementById('isi_suratMasuk').value.trim()
        };

        // Validasi field wajib
        const requiredFields = {
            "Nomor Surat Lengkap": formData.full_letter_number,
            "Pengirim": formData.pengirim_suratMasuk,
            "Penerima": formData.penerima_suratMasuk,
            "Isi": formData.isi_suratMasuk,
            "Tanggal Surat": formData.selected_date
        };
        
        const missingFields = [];
        for (const [fieldName, value] of Object.entries(requiredFields)) {
            if (!value) {
                missingFields.push(fieldName);
            }
        }
        
        if (missingFields.length > 0) {
            alert(`Harap isi semua field wajib:\n- ${missingFields.join('\n- ')}`);
            saveButton.innerHTML = originalButtonText;
            saveButton.disabled = false;
            return;
        }

        fetch("{{ url_for('ocr_surat_masuk.ocr_surat_masuk') }}", {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
                "X-Requested-With": "XMLHttpRequest"  // Tandai sebagai AJAX
            },
            body: new URLSearchParams(formData),
        })
        .then(response => {
            // Tanggapan mungkin bukan JSON (misal: error 500)
            const contentType = response.headers.get("content-type");
            if (contentType && contentType.includes("application/json")) {
                return response.json();
            } else {
                return response.text().then(text => {
                    // Periksa apakah respons adalah halaman login (session habis)
                    if (text.includes("login")) {
                        return { 
                            success: false, 
                            error: "Sesi Anda telah habis. Silakan login kembali." 
                        };
                    }
                    throw new Error(text || "Respons tidak valid dari server");
                });
            }
        })
        .then(data => {
            console.log("Server response:", data);
            if (data.success) {
                // Auto navigate to next entry
                if (currentIndex < extractedDataList.length - 1) {
                    openModal(currentIndex + 1);
                } else {
                    $('#dataModal').modal('hide');
                    alert('Semua data berhasil disimpan!');
                    // Optional: reload the page to reset the state
                    window.location.reload();
                }
            } else {
                // Tampilkan error spesifik dari server jika ada
                const errorMsg = data.error || "Kesalahan tidak diketahui";
                alert(`Gagal menyimpan data: ${errorMsg}`);
            }
        })
        .catch(error => {
            console.error("Error:", error);
            alert(`Terjadi kesalahan: ${error.message || error}`);
        })
        .finally(() => {
            saveButton.innerHTML = originalButtonText;
            saveButton.disabled = false;
        });
    }

    // Fungsi zoom gambar
    let scale = 1;
    let originX = 0;
    let originY = 0;
    let startX, startY;
    let isDragging = false;

    const image = document.getElementById("modal-image");
    const imageContainer = document.querySelector(".image-container");

    imageContainer.addEventListener("wheel", function (e) {
        e.preventDefault();
        const scaleAmount = 0.1;
        const rect = imageContainer.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;
        
        if (e.deltaY < 0) {
            scale += scaleAmount;
        } else {
            scale = Math.max(scale - scaleAmount, 0.1);
        }
        
        // Sesuaikan origin untuk zoom di posisi kursor
        originX = mouseX - (mouseX - originX) * (scale / (scale - scaleAmount));
        originY = mouseY - (mouseY - originY) * (scale / (scale - scaleAmount));
        
        updateTransform();
    });

    imageContainer.addEventListener("mousedown", function (e) {
        isDragging = true;
        startX = e.clientX - originX;
        startY = e.clientY - originY;
        imageContainer.style.cursor = "grabbing";
    });

    document.addEventListener("mousemove", function (e) {
        if (isDragging) {
            originX = e.clientX - startX;
            originY = e.clientY - startY;
            updateTransform();
        }
    });

    document.addEventListener("mouseup", function () {
        isDragging = false;
        imageContainer.style.cursor = "grab";
    });

    function updateTransform() {
        image.style.transform = `translate(${originX}px, ${originY}px) scale(${scale})`;
    }

    function resetZoom() {
        scale = 1;
        originX = 0;
        originY = 0;
        updateTransform();
    }

    function zoomIn() {
        scale += 0.2;
        updateTransform();
    }

    function zoomOut() {
        scale = Math.max(scale - 0.2, 0.5);
        updateTransform();
    }