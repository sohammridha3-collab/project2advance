/**
 * Prescription Vault & Collection Logic
 * Supports secure multipart upload, preview, structured clinical fields,
 * responsive cards, detailed inspection modal, and medicine management.
 */
(() => {
  "use strict";

  const { prescriptions, auth } = window.HR_API;
  const { showToast, ensureAuth, openAuthModal } = window.HR_UI;
  const { esc } = window.HR || { esc: (s) => String(s || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;") };

  const ALLOWED_EXTS = [".pdf", ".jpg", ".jpeg", ".png"];
  const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10 MB

  // DOM Elements - Upload & Dual Options
  const uploadSection = document.getElementById("vault-upload-section");
  const uploadForm = document.getElementById("vault-upload-form");
  const optionsContainer = document.getElementById("vault-options-container");
  const cameraCard = document.getElementById("camera-option-card");
  const deviceCard = document.getElementById("device-option-card");
  const startCameraBtn = document.getElementById("start-camera-btn");
  const cameraFileInput = document.getElementById("camera-file-input");
  const dropzone = document.getElementById("vault-dropzone");
  const fileInput = document.getElementById("prescription-file-input");
  const triggerFileBtn = document.getElementById("trigger-file-btn");

  // DOM Elements - Preview
  const previewCard = document.getElementById("dropzone-file-preview");
  const previewThumbBox = document.getElementById("preview-thumb-box");
  const previewFilename = document.getElementById("preview-filename");
  const previewFilesize = document.getElementById("preview-filesize");
  const previewFiletype = document.getElementById("preview-filetype");
  const previewSourceBadge = document.getElementById("preview-source-badge");
  const retakePhotoBtn = document.getElementById("retake-photo-btn");
  const replaceFileBtn = document.getElementById("replace-file-btn");
  const removeFileBtn = document.getElementById("remove-file-btn");
  const cancelUploadBtn = document.getElementById("cancel-upload-btn");
  const submitVaultBtn = document.getElementById("submit-vault-btn");
  const uploadStatus = document.getElementById("vault-upload-status");
  const medsContainer = document.getElementById("medicines-container");
  const addMedRowBtn = document.getElementById("add-med-row-btn");
  const uploadProgressBarWrap = document.getElementById("vault-upload-progress");
  const uploadProgressText = document.getElementById("upload-progress-text");
  const uploadProgressPercent = document.getElementById("upload-progress-percent");
  const uploadProgressBar = document.getElementById("upload-progress-bar");

  // DOM Elements - Live Camera Viewfinder Modal
  const cameraModal = document.getElementById("camera-modal");
  const cameraVideo = document.getElementById("camera-video");
  const cameraCanvas = document.getElementById("camera-canvas");
  const closeCameraModalBtn = document.getElementById("close-camera-modal-btn");
  const switchCameraBtn = document.getElementById("switch-camera-btn");
  const shutterBtn = document.getElementById("shutter-btn");
  const cameraCancelBtn = document.getElementById("camera-cancel-btn");
  const cameraLoadingOverlay = document.getElementById("camera-loading-overlay");
  const cameraStatusText = document.getElementById("camera-status-text");
  const cameraErrorOverlay = document.getElementById("camera-error-overlay");
  const cameraErrorDesc = document.getElementById("camera-error-desc");
  const fallbackCaptureBtn = document.getElementById("fallback-capture-btn");
  const cameraErrorDismissBtn = document.getElementById("camera-error-dismiss-btn");
  const cameraDeviceFallbackBtn = document.getElementById("camera-device-fallback-btn");

  // DOM Elements - Collection
  const listContainer = document.getElementById("vault-list-container");
  const countBadge = document.getElementById("vault-count-badge");

  // DOM Elements - Details Modal
  const detailModal = document.getElementById("prescription-detail-modal");
  const detailModalTitle = document.getElementById("modal-presc-title");
  const detailModalBody = document.getElementById("modal-presc-body");
  const closeDetailModalBtn = document.getElementById("close-detail-modal-btn");
  const modalCloseBtn = document.getElementById("modal-close-btn");
  const modalDeletePrescBtn = document.getElementById("modal-delete-presc-btn");
  const modalEditToggleBtn = document.getElementById("modal-edit-toggle-btn");
  const modalFileLinkContainer = document.getElementById("modal-file-link-container");

  // DOM Elements - Confirm Delete Modal
  const confirmDeleteModal = document.getElementById("confirm-delete-modal");
  const cancelDeleteModalBtn = document.getElementById("cancel-delete-modal-btn");
  const abortDeleteBtn = document.getElementById("abort-delete-btn");
  const executeDeleteBtn = document.getElementById("execute-delete-btn");

  let selectedFile = null;
  let activePrescriptionIdToDelete = null;
  let currentDetailPrescription = null;
  let isEditingDetails = false;

  // Live Camera State
  let activeCameraStream = null;
  let currentFacingMode = "environment"; // Prefer rear-facing camera on mobile
  let capturedSource = "device"; // 'camera' or 'device'

  // Format Helper
  function formatDate(isoStr) {
    if (!isoStr) return "Not specified";
    try {
      const dt = new Date(isoStr);
      if (isNaN(dt.getTime())) return isoStr;
      return dt.toLocaleDateString("en-US", {
        day: "2-digit",
        month: "short",
        year: "numeric"
      });
    } catch {
      return isoStr;
    }
  }

  function formatFileSize(bytes) {
    if (!bytes || bytes === 0) return "0 MB";
    const mb = bytes / (1024 * 1024);
    return `${mb.toFixed(2)} MB`;
  }

  // ============================================================
  // LIVE CAMERA CONTROLLER (Option A)
  // ============================================================
  async function startCameraCapture() {
    // Check browser compatibility
    const hasMediaDevices = !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);

    // If browser doesn't support getUserMedia or context is non-secure without localhost,
    // seamlessly trigger device camera app via native capture="environment" file input
    if (!hasMediaDevices) {
      if (cameraFileInput) {
        cameraFileInput.click();
      } else if (fileInput) {
        fileInput.click();
      }
      return;
    }

    if (cameraModal) {
      cameraModal.style.display = "flex";
      cameraModal.classList.add("active");
    }
    if (cameraLoadingOverlay) {
      cameraLoadingOverlay.style.display = "flex";
      if (cameraStatusText) cameraStatusText.textContent = "Starting camera...";
    }
    if (cameraErrorOverlay) cameraErrorOverlay.style.display = "none";

    stopCameraStream();

    try {
      // 1. Prefer rear-facing camera on mobile devices with high definition
      const constraints = {
        video: {
          facingMode: { ideal: currentFacingMode },
          width: { ideal: 1920 },
          height: { ideal: 1080 }
        },
        audio: false
      };

      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      attachStreamToVideo(stream);
      await checkMultipleCameras();
    } catch (err) {
      console.warn("Primary camera constraints failed, attempting fallback:", err);
      try {
        // 2. Fallback to basic video request
        const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        attachStreamToVideo(stream);
        await checkMultipleCameras();
      } catch (fallbackErr) {
        console.error("Camera access failed:", fallbackErr);
        if (cameraLoadingOverlay) cameraLoadingOverlay.style.display = "none";
        if (cameraErrorOverlay) {
          cameraErrorOverlay.style.display = "flex";
          if (cameraErrorDesc) {
            const isDenied = fallbackErr.name === "NotAllowedError" || fallbackErr.name === "PermissionDeniedError";
            cameraErrorDesc.textContent = isDenied
              ? "Camera permission was denied in your browser. You can allow camera access in browser settings, or tap below to photograph using your device camera app."
              : `Unable to open live camera (${fallbackErr.message || "Device unavailable"}). You can take a photo using your device's native camera.`;
          }
        }
      }
    }
  }

  function attachStreamToVideo(stream) {
    activeCameraStream = stream;
    if (cameraVideo) {
      cameraVideo.srcObject = stream;
      cameraVideo.play().catch(e => console.warn("Video play error:", e));
    }
    if (cameraLoadingOverlay) cameraLoadingOverlay.style.display = "none";
  }

  function stopCameraStream() {
    if (activeCameraStream) {
      activeCameraStream.getTracks().forEach((track) => {
        try {
          track.stop();
        } catch (e) {
          console.warn("Track stop error:", e);
        }
      });
      activeCameraStream = null;
    }
    if (cameraVideo) {
      cameraVideo.srcObject = null;
    }
  }

  function closeCameraModal() {
    stopCameraStream();
    if (cameraModal) {
      cameraModal.style.display = "none";
      cameraModal.classList.remove("active");
    }
    if (cameraLoadingOverlay) cameraLoadingOverlay.style.display = "none";
    if (cameraErrorOverlay) cameraErrorOverlay.style.display = "none";
  }

  async function switchCamera() {
    currentFacingMode = currentFacingMode === "environment" ? "user" : "environment";
    await startCameraCapture();
  }

  async function checkMultipleCameras() {
    if (!switchCameraBtn) return;
    try {
      if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {
        const devices = await navigator.mediaDevices.enumerateDevices();
        const videoDevices = devices.filter(d => d.kind === "videoinput");
        switchCameraBtn.style.display = videoDevices.length > 1 ? "inline-flex" : "none";
      } else {
        switchCameraBtn.style.display = "none";
      }
    } catch {
      switchCameraBtn.style.display = "none";
    }
  }

  function capturePhotoFromVideo() {
    if (!cameraVideo || !activeCameraStream || cameraVideo.videoWidth === 0) {
      showToast("Camera feed is not ready yet. Please wait a moment.", "warning");
      return;
    }

    const width = cameraVideo.videoWidth || 1280;
    const height = cameraVideo.videoHeight || 960;
    cameraCanvas.width = width;
    cameraCanvas.height = height;

    const ctx = cameraCanvas.getContext("2d");
    ctx.drawImage(cameraVideo, 0, 0, width, height);

    cameraCanvas.toBlob((blob) => {
      if (!blob) {
        showToast("Failed to snapshot photo from camera.", "error");
        return;
      }

      const timestamp = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);
      const photoFile = new File([blob], `prescription_photo_${timestamp}.jpg`, {
        type: "image/jpeg",
        lastModified: Date.now()
      });

      closeCameraModal();
      handleFileSelection(photoFile, { source: "camera" });
      showToast("Prescription photo captured! Review preview below.", "success");
    }, "image/jpeg", 0.92);
  }

  // ============================================================
  // FILE SELECTION, CAMERA CAPTURE HANDLING, AND PREVIEW
  // ============================================================
  const extractOcrBtn = document.getElementById("extract-ocr-btn");
  const extractionBanner = document.getElementById("vault-extraction-banner");
  const extractionStatusTitle = document.getElementById("extraction-status-title");
  const extractionStatusDesc = document.getElementById("extraction-status-desc");

  function handleFileSelection(file, options = {}) {
    if (!file) return;

    const ext = "." + (file.name || "").split(".").pop().toLowerCase();
    if (!ALLOWED_EXTS.includes(ext)) {
      showToast(`Invalid file format '${ext}'. Allowed: ${ALLOWED_EXTS.join(", ")}`, "error");
      if (fileInput) fileInput.value = "";
      if (cameraFileInput) cameraFileInput.value = "";
      return;
    }

    if (file.size > MAX_FILE_SIZE) {
      showToast("File size exceeds 10 MB limit.", "error");
      if (fileInput) fileInput.value = "";
      if (cameraFileInput) cameraFileInput.value = "";
      return;
    }

    selectedFile = file;

    // Show preview card with file info
    if (previewFilename) previewFilename.textContent = file.name;
    if (previewFilesize) previewFilesize.textContent = formatFileSize(file.size);

    const isPdf = ext === ".pdf";
    if (previewFiletype) previewFiletype.textContent = isPdf ? "PDF Document" : "Image (JPEG/PNG)";

    // Update Source Badge & Retake Button
    const isCamera = options.source === "camera";
    capturedSource = isCamera ? "camera" : "device";
    if (previewSourceBadge) {
      previewSourceBadge.textContent = isCamera ? "📸 Camera Capture" : "📁 Device Upload";
      previewSourceBadge.style.display = "inline-flex";
    }
    if (retakePhotoBtn) {
      retakePhotoBtn.style.display = isCamera ? "inline-flex" : "none";
    }

    // Generate Thumbnail
    if (previewThumbBox) {
      previewThumbBox.innerHTML = "";
      if (isPdf) {
        previewThumbBox.innerHTML = `<span class="pdf-icon-badge" title="PDF Document" style="font-size:2rem">📄</span>`;
      } else {
        const img = document.createElement("img");
        img.alt = file.name;
        img.className = "vault-preview-thumbnail";
        const reader = new FileReader();
        reader.onload = (e) => {
          img.src = e.target.result;
        };
        reader.readAsDataURL(file);
        previewThumbBox.appendChild(img);
      }
    }

    // Auto-fill Title if currently empty
    const titleInput = document.getElementById("vault-title");
    if (titleInput && !titleInput.value.trim()) {
      if (isCamera) {
        const todayStr = new Date().toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
        titleInput.value = `Camera Prescription - ${todayStr}`;
      } else {
        const cleanBase = file.name.replace(/\.[^/.]+$/, "").replace(/[_\-]+/g, " ");
        titleInput.value = cleanBase.charAt(0).toUpperCase() + cleanBase.slice(1);
      }
    }

    if (dropzone) dropzone.style.display = "none";
    if (previewCard) previewCard.style.display = "flex";
  }

  function resetSelectedFile() {
    selectedFile = null;
    if (fileInput) fileInput.value = "";
    if (cameraFileInput) cameraFileInput.value = "";
    if (previewCard) previewCard.style.display = "none";
    if (dropzone) dropzone.style.display = "flex";
    if (previewThumbBox) previewThumbBox.innerHTML = "";
    if (previewSourceBadge) previewSourceBadge.style.display = "none";
    if (retakePhotoBtn) retakePhotoBtn.style.display = "none";
    if (extractionBanner) extractionBanner.style.display = "none";
  }

  async function triggerOcrExtraction() {
    if (!selectedFile) {
      showToast("Please choose or photograph a prescription first.", "warning");
      return;
    }

    if (extractOcrBtn) {
      extractOcrBtn.disabled = true;
      extractOcrBtn.textContent = "⏳ Extracting...";
    }

    try {
      showToast("Analyzing prescription document with AI...", "info");
      const fd = new FormData();
      fd.append("file", selectedFile);
      const res = await prescriptions.extract(fd);

      if (res && res.extracted_data) {
        const d = res.extracted_data;
        const titleInput = document.getElementById("vault-title");
        const dateInput = document.getElementById("vault-date");
        const docInput = document.getElementById("vault-doctor");
        const hospInput = document.getElementById("vault-hospital");
        const diagInput = document.getElementById("vault-diagnosis");
        const probInput = document.getElementById("vault-problem");

        if (d.title && titleInput && !titleInput.value) {
          titleInput.value = d.title;
        }
        if (d.prescription_date && dateInput && !dateInput.value) {
          dateInput.value = d.prescription_date;
        }
        if (d.doctor_name && docInput && !docInput.value) {
          docInput.value = d.doctor_name;
        }
        if (d.hospital_name && hospInput && !hospInput.value) {
          hospInput.value = d.hospital_name;
        }
        if (d.diagnosis && diagInput && !diagInput.value) {
          diagInput.value = d.diagnosis;
        }
        if (d.main_health_problem && probInput && !probInput.value) {
          probInput.value = d.main_health_problem;
        }

        // Populate medicine candidates if none entered yet
        if (Array.isArray(d.medicines) && d.medicines.length > 0) {
          if (medsContainer.querySelectorAll(".med-row").length === 0) {
            d.medicines.forEach(m => createMedicineRow(m));
          }
        }

        if (extractionBanner) {
          extractionBanner.style.display = "flex";
          if (extractionStatusTitle) {
            extractionStatusTitle.textContent = `Candidate details extracted (Status: ${d.status || 'unverified'})`;
          }
          if (extractionStatusDesc) {
            extractionStatusDesc.textContent = res.notice || "Please review and edit all candidate fields before saving.";
          }
        }
        showToast("Extracted candidate details! Review before saving.", "success");
      }
    } catch (err) {
      console.warn("Extraction warning:", err);
      showToast(err.message || "Document extraction could not parse text. You can still enter details manually.", "warning");
    } finally {
      if (extractOcrBtn) {
        extractOcrBtn.disabled = false;
        extractOcrBtn.textContent = "✨ Extract with AI";
      }
    }
  }

  // Bind Camera Action Buttons
  if (startCameraBtn) {
    startCameraBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      startCameraCapture();
    });
  }

  if (cameraCard) {
    cameraCard.addEventListener("click", (e) => {
      if (e.target.closest("button") || e.target.closest("input")) return;
      startCameraCapture();
    });
    cameraCard.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        startCameraCapture();
      }
    });
  }

  if (deviceCard) {
    deviceCard.addEventListener("click", (e) => {
      if (e.target.closest("button") || e.target.closest("input")) return;
      if (fileInput) fileInput.click();
    });
    deviceCard.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        if (fileInput) fileInput.click();
      }
    });
  }

  if (triggerFileBtn) {
    triggerFileBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      if (fileInput) fileInput.click();
    });
  }

  if (cameraFileInput) {
    cameraFileInput.addEventListener("change", (e) => {
      if (e.target.files && e.target.files[0]) {
        handleFileSelection(e.target.files[0], { source: "camera" });
      }
    });
  }

  if (fileInput) {
    fileInput.addEventListener("change", (e) => {
      if (e.target.files && e.target.files[0]) {
        handleFileSelection(e.target.files[0], { source: "device" });
      }
    });
  }

  // Camera Viewfinder Controls
  if (shutterBtn) {
    shutterBtn.addEventListener("click", capturePhotoFromVideo);
  }

  if (closeCameraModalBtn) {
    closeCameraModalBtn.addEventListener("click", closeCameraModal);
  }

  if (cameraCancelBtn) {
    cameraCancelBtn.addEventListener("click", closeCameraModal);
  }

  if (switchCameraBtn) {
    switchCameraBtn.addEventListener("click", switchCamera);
  }

  if (fallbackCaptureBtn) {
    fallbackCaptureBtn.addEventListener("click", () => {
      closeCameraModal();
      if (cameraFileInput) cameraFileInput.click();
    });
  }

  if (cameraErrorDismissBtn) {
    cameraErrorDismissBtn.addEventListener("click", closeCameraModal);
  }

  if (cameraDeviceFallbackBtn) {
    cameraDeviceFallbackBtn.addEventListener("click", () => {
      closeCameraModal();
      if (fileInput) fileInput.click();
    });
  }

  if (cameraModal) {
    cameraModal.addEventListener("click", (e) => {
      if (e.target === cameraModal) closeCameraModal();
    });
  }

  // Preview Card Controls
  if (retakePhotoBtn) {
    retakePhotoBtn.addEventListener("click", startCameraCapture);
  }

  if (replaceFileBtn) {
    replaceFileBtn.addEventListener("click", () => {
      if (capturedSource === "camera") {
        startCameraCapture();
      } else if (fileInput) {
        fileInput.click();
      }
    });
  }

  if (removeFileBtn) {
    removeFileBtn.addEventListener("click", resetSelectedFile);
  }

  if (extractOcrBtn) {
    extractOcrBtn.addEventListener("click", triggerOcrExtraction);
  }

  // Dropzone Events
  if (dropzone) {
    dropzone.addEventListener("click", () => {
      if (fileInput) fileInput.click();
    });
    dropzone.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        if (fileInput) fileInput.click();
      }
    });

    ["dragenter", "dragover"].forEach((evtName) => {
      dropzone.addEventListener(evtName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.add("dragover");
      });
    });

    ["dragleave", "drop"].forEach((evtName) => {
      dropzone.addEventListener(evtName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.remove("dragover");
      });
    });

    dropzone.addEventListener("drop", (e) => {
      if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0]) {
        handleFileSelection(e.dataTransfer.files[0], { source: "device" });
      }
    });
  }

  // ============================================================
  // MEDICINES REPEATER IN UPLOAD FORM
  // ============================================================
  function createMedicineRow(data = {}) {
    const row = document.createElement("div");
    row.className = "med-row";
    row.innerHTML = `
      <input type="text" class="med-name" placeholder="Medicine name (e.g. Amlodipine)" value="${esc(data.medicine_name || '')}" required>
      <input type="text" class="med-dosage" placeholder="Dosage (e.g. 5 mg)" value="${esc(data.dosage || '')}">
      <input type="text" class="med-freq" placeholder="Frequency (e.g. Once daily)" value="${esc(data.frequency || '')}">
      <input type="text" class="med-dur" placeholder="Duration (e.g. 30 days)" value="${esc(data.duration || '')}">
      <div class="del-col" style="text-align:right">
        <button type="button" class="btn btn-sm btn-danger remove-med-btn" title="Remove medicine">&times;</button>
      </div>
    `;

    row.querySelector(".remove-med-btn").addEventListener("click", () => row.remove());
    medsContainer.appendChild(row);
  }

  if (addMedRowBtn) {
    addMedRowBtn.addEventListener("click", () => createMedicineRow());
  }

  // Upload Progress helper
  function setUploadProgress(percent, label) {
    if (!uploadProgressBarWrap) return;
    if (percent === null) {
      uploadProgressBarWrap.style.display = "none";
      if (uploadProgressBar) uploadProgressBar.style.width = "0%";
      return;
    }
    uploadProgressBarWrap.style.display = "block";
    uploadProgressBarWrap.setAttribute("aria-valuenow", percent);
    if (uploadProgressPercent) uploadProgressPercent.textContent = `${percent}%`;
    if (uploadProgressBar) uploadProgressBar.style.width = `${percent}%`;
    if (label && uploadProgressText) uploadProgressText.textContent = label;
  }

  // Cancel Upload Form
  if (cancelUploadBtn) {
    cancelUploadBtn.addEventListener("click", () => {
      uploadForm.reset();
      resetSelectedFile();
      medsContainer.innerHTML = "";
      setUploadProgress(null);
      uploadStatus.style.display = "none";
      showToast("Upload cancelled.", "info");
    });
  }

  // ============================================================
  // SUBMIT PRESCRIPTION UPLOAD
  // ============================================================
  if (uploadForm) {
    uploadForm.addEventListener("submit", async (e) => {
      e.preventDefault();

      ensureAuth("save to your prescription vault", async () => {
        submitVaultBtn.disabled = true;
        submitVaultBtn.innerHTML = `<span>⏳</span> Saving...`;
        uploadStatus.style.display = "flex";
        uploadStatus.className = "form-state-box info";
        uploadStatus.innerHTML = `<span>⏳</span><span>Validating and saving prescription to your secure vault...</span>`;
        setUploadProgress(20, "Encrypting & preparing upload...");

        try {
          const title = document.getElementById("vault-title") ? document.getElementById("vault-title").value.trim() : "";
          const date = document.getElementById("vault-date").value;
          const problem = document.getElementById("vault-problem").value.trim();
          const doctor = document.getElementById("vault-doctor").value.trim();
          const hospital = document.getElementById("vault-hospital").value.trim();
          const diagnosis = document.getElementById("vault-diagnosis").value.trim();
          const notes = document.getElementById("vault-notes").value.trim();

          // Collect medicines
          const medRows = medsContainer.querySelectorAll(".med-row");
          const medsList = [];
          medRows.forEach((r) => {
            const name = r.querySelector(".med-name").value.trim();
            if (name) {
              medsList.push({
                medicine_name: name,
                dosage: r.querySelector(".med-dosage").value.trim() || null,
                frequency: r.querySelector(".med-freq").value.trim() || null,
                duration: r.querySelector(".med-dur").value.trim() || null,
                instructions: null
              });
            }
          });

          // Check if at least a photo/file OR basic details was provided
          if (!selectedFile && !title && !problem && !doctor && medsList.length === 0) {
            showToast("Please capture a photo or provide prescription details to save.", "warning");
            submitVaultBtn.disabled = false;
            submitVaultBtn.innerHTML = `Save Prescription`;
            uploadStatus.style.display = "none";
            setUploadProgress(null);
            return;
          }

          const formData = new FormData();
          if (selectedFile) {
            formData.append("file", selectedFile);
          }

          if (title) {
            formData.append("title", title);
          } else if (selectedFile) {
            formData.append("title", `Prescription - ${date || new Date().toISOString().split("T")[0]}`);
          }

          if (date) formData.append("prescription_date", date);
          if (problem) formData.append("main_health_problem", problem);
          if (doctor) formData.append("doctor_name", doctor);
          if (hospital) formData.append("hospital_name", hospital);
          if (diagnosis) formData.append("diagnosis", diagnosis);
          if (notes) formData.append("notes", notes);


          if (medsList.length > 0) {
            formData.append("medicines", JSON.stringify(medsList));
          }

          setUploadProgress(55, "Uploading prescription document to vault...");
          await prescriptions.upload(formData);
          setUploadProgress(100, "Prescription saved and verified!");

          uploadStatus.className = "form-state-box success";
          uploadStatus.innerHTML = `<span>✓</span><span>Prescription saved successfully to your vault!</span>`;
          showToast("Prescription stored in Vault successfully!", "success");

          // Reset form & file
          uploadForm.reset();
          resetSelectedFile();
          medsContainer.innerHTML = "";

          // Set default date to today for subsequent entry
          const today = new Date().toISOString().split("T")[0];
          document.getElementById("vault-date").value = today;

          setTimeout(() => {
            uploadStatus.style.display = "none";
            setUploadProgress(null);
          }, 3500);

          await loadPrescriptionsCollection();
        } catch (err) {
          setUploadProgress(null);
          uploadStatus.className = "form-state-box error";
          uploadStatus.innerHTML = `<span>⚠</span><span>${esc(err.message)}</span>`;
          showToast(err.message || "Failed to save prescription", "error");
        } finally {
          submitVaultBtn.disabled = false;
          submitVaultBtn.innerHTML = `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:18px;height:18px">
              <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>
              <polyline points="17 21 17 13 7 13 7 21"/>
              <polyline points="7 3 7 8 15 8"/>
            </svg>
            Save Prescription
          `;
        }
      });
    });
  }

  // ============================================================
  // LOAD & RENDER MY PRESCRIPTIONS COLLECTION (Section 2.B)
  // ============================================================
  async function loadPrescriptionsCollection() {
    if (!auth.isAuthenticated()) {
      listContainer.innerHTML = `
        <div class="glass empty-card" style="grid-column: 1 / -1; text-align:center; padding: 3rem 1.5rem;">
          <span class="chip-ico" style="margin:0 auto 1rem">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="ico">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
              <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
            </svg>
          </span>
          <h3 style="margin-top:0">Sign In to Access Your Vault</h3>
          <p style="color:var(--mute);margin-bottom:1.2rem">Your prescription records and documents are encrypted and accessible only with your account.</p>
          <button id="vault-auth-btn" class="btn p" type="button">Sign In / Register</button>
        </div>
      `;
      const authBtn = document.getElementById("vault-auth-btn");
      if (authBtn) {
        authBtn.addEventListener("click", () => openAuthModal("login", loadPrescriptionsCollection));
      }
      if (countBadge) countBadge.textContent = "";
      return;
    }

    listContainer.innerHTML = `
      <div class="glass empty-card" style="grid-column: 1 / -1; text-align:center; padding: 3rem 1.5rem;">
        <p>Loading prescription vault records...</p>
      </div>
    `;

    try {
      const items = await prescriptions.list();

      if (!items || items.length === 0) {
        if (countBadge) countBadge.textContent = "0 Prescriptions";
        listContainer.innerHTML = `
          <div class="glass empty-card" style="grid-column: 1 / -1; text-align:center; padding: 3rem 1.5rem;">
            <span class="chip-ico" style="margin:0 auto 1rem">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="ico">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
                <line x1="12" y1="18" x2="12" y2="12"/>
                <line x1="9" y1="15" x2="15" y2="15"/>
              </svg>
            </span>
            <h3 style="margin-top:0">No Prescriptions in Vault</h3>
            <p style="color:var(--mute);margin-bottom:1.4rem">You have not saved any prescriptions yet. Upload your first clinical prescription above to start your collection.</p>
            <button id="scroll-to-upload-btn" class="btn p" type="button">
              + Upload Prescription
            </button>
          </div>
        `;
        const scrollBtn = document.getElementById("scroll-to-upload-btn");
        if (scrollBtn) {
          scrollBtn.addEventListener("click", () => {
            uploadSection.scrollIntoView({ behavior: "smooth" });
            fileInput.click();
          });
        }
        return;
      }

      if (countBadge) {
        countBadge.textContent = `${items.length} Saved Prescription${items.length === 1 ? '' : 's'}`;
      }

      listContainer.innerHTML = items.map((p) => {
        const fileUrl = p.file_path ? prescriptions.getFileUrl(p.id) : null;
        const isPdf = p.file_path && p.file_path.toLowerCase().endsWith(".pdf");
        const isImg = p.file_path && /\.(jpg|jpeg|png)$/i.test(p.file_path);
        const meds = p.medicines || [];

        // Preview thumbnail markup
        let thumbHtml = `
          <div class="presc-card-thumb">
            <span style="font-size:1.6rem">📋</span>
          </div>
        `;
        if (isImg && fileUrl) {
          thumbHtml = `
            <div class="presc-card-thumb">
              <img src="${fileUrl}" alt="Prescription thumbnail" loading="lazy">
            </div>
          `;
        } else if (isPdf) {
          thumbHtml = `
            <div class="presc-card-thumb" title="PDF Document">
              <span style="font-size:1.6rem">📄</span>
            </div>
          `;
        }

        const prescTitle = p.title || p.main_health_problem || p.diagnosis || "Medical Prescription";
        const primaryProblem = p.main_health_problem || p.diagnosis || "General Clinical Record";
        const dateStr = formatDate(p.prescription_date || p.created_at);

        // Medicines chips
        const medChipsHtml = meds.length > 0
          ? meds.slice(0, 3).map(m => `<span class="presc-med-chip">💊 ${esc(m.medicine_name)}${m.dosage ? ` (${esc(m.dosage)})` : ''}</span>`).join("") +
            (meds.length > 3 ? `<span class="presc-med-chip">+${meds.length - 3} more</span>` : '')
          : `<span style="font-size:.8rem;color:var(--mute);font-style:italic">No medicines recorded</span>`;

        return `
          <div class="presc-card glass tilt" id="prescription-card-${p.id}" data-id="${p.id}" tabindex="0" role="article" aria-label="Prescription ${esc(prescTitle)} from ${dateStr}">
            <div>
              <div class="presc-card-top">
                ${thumbHtml}
                <div class="presc-card-meta">
                  <span class="presc-card-date-badge">📅 ${dateStr}</span>
                  <h3 class="presc-card-problem" title="${esc(prescTitle)}">${esc(prescTitle)}</h3>
                  <p class="presc-card-doctor">👨‍⚕️ ${esc(p.doctor_name || "Doctor unspecified")}</p>
                  ${p.main_health_problem ? `<div class="presc-card-hospital" style="color:var(--aqua)">🩺 ${esc(p.main_health_problem)}</div>` : ''}
                  ${p.hospital_name ? `<div class="presc-card-hospital">🏥 ${esc(p.hospital_name)}</div>` : ''}
                </div>
              </div>

              <div class="presc-card-meds-summary">
                ${medChipsHtml}
              </div>
            </div>

            <div class="presc-card-footer">
              <button class="btn btn-sm p view-presc-details-btn" data-id="${p.id}" type="button">
                View Details
              </button>
              <div style="display:flex;gap:.4rem;align-items:center;flex-wrap:wrap">
                <button class="btn btn-sm edit-presc-btn" data-id="${p.id}" type="button" title="Edit prescription details">
                  ✏️ Edit
                </button>
                ${fileUrl ? `<a href="${fileUrl}" target="_blank" rel="noopener noreferrer" class="btn btn-sm" title="View prescription document">👁️ View</a>` : ''}
                ${fileUrl ? `<a href="${fileUrl}&download=true" download="${esc(p.original_filename || 'prescription')}" class="btn btn-sm" title="Download prescription file">⬇️ Download</a>` : ''}
                <button class="btn btn-sm btn-danger delete-presc-btn" data-id="${p.id}" type="button" title="Delete prescription">
                  Delete
                </button>
              </div>
            </div>
          </div>
        `;
      }).join("");

      // Bind Card Click (anywhere except interactive elements)
      listContainer.querySelectorAll(".presc-card").forEach((card) => {
        card.addEventListener("click", (e) => {
          if (e.target.closest("button") || e.target.closest("a") || e.target.closest("input")) return;
          const id = card.getAttribute("data-id");
          if (id) openPrescriptionDetailModal(id, false);
        });
        card.addEventListener("keydown", (e) => {
          if (e.key === "Enter" || e.key === " ") {
            if (e.target.closest("button") || e.target.closest("a") || e.target.closest("input")) return;
            e.preventDefault();
            const id = card.getAttribute("data-id");
            if (id) openPrescriptionDetailModal(id, false);
          }
        });
      });

      // Bind Details click
      listContainer.querySelectorAll(".view-presc-details-btn").forEach((btn) => {
        btn.addEventListener("click", (e) => {
          e.stopPropagation();
          openPrescriptionDetailModal(btn.dataset.id, false);
        });
      });

      // Bind Edit click on card
      listContainer.querySelectorAll(".edit-presc-btn").forEach((btn) => {
        btn.addEventListener("click", (e) => {
          e.stopPropagation();
          openPrescriptionDetailModal(btn.dataset.id, true);
        });
      });

      // Bind Delete click
      listContainer.querySelectorAll(".delete-presc-btn").forEach((btn) => {
        btn.addEventListener("click", (e) => {
          e.stopPropagation();
          promptDeletePrescription(btn.dataset.id);
        });
      });
    } catch (err) {
      listContainer.innerHTML = `
        <div class="glass empty-card" style="grid-column: 1 / -1; text-align:center; padding: 3rem 1.5rem;">
          <p style="color:var(--crit);margin-bottom:1rem">Failed to load prescriptions: ${esc(err.message)}</p>
          <button class="btn" type="button" onclick="location.reload()">Retry</button>
        </div>
      `;
    }
  }

  // ============================================================
  // PRESCRIPTION DETAILS & STRUCTURED COLLECTION (Section 2.C)
  // ============================================================
  async function openPrescriptionDetailModal(id, startInEditMode = false) {
    detailModal.classList.add("active");
    detailModalTitle.textContent = "Loading prescription details...";
    detailModalBody.innerHTML = `<div style="text-align:center;padding:2.5rem"><p>Retrieving structured clinical records...</p></div>`;
    modalFileLinkContainer.innerHTML = "";
    isEditingDetails = !!startInEditMode;
    modalEditToggleBtn.textContent = isEditingDetails ? "Hide Edit Form" : "Edit Details";

    try {
      const p = await prescriptions.get(id);
      currentDetailPrescription = p;
      renderPrescriptionDetailsView(p);
    } catch (err) {
      detailModalBody.innerHTML = `<p style="color:var(--crit);padding:1.5rem">Error: ${esc(err.message)}</p>`;
    }
  }

  function renderPrescriptionDetailsView(p) {
    detailModalTitle.innerHTML = `<span>📋</span> Prescription Details #${p.id}`;

    const fileUrl = p.file_path ? prescriptions.getFileUrl(p.id) : null;
    if (fileUrl) {
      modalFileLinkContainer.innerHTML = `
        <div style="display:flex;gap:.5rem;align-items:center;flex-wrap:wrap">
          <a href="${fileUrl}" target="_blank" rel="noopener noreferrer" class="btn btn-sm" style="display:inline-flex;align-items:center;gap:.4rem">
            <span>👁️</span> View Document
          </a>
          <a href="${fileUrl}&download=true" download="${esc(p.original_filename || 'prescription')}" class="btn btn-sm p" style="display:inline-flex;align-items:center;gap:.4rem">
            <span>⬇️</span> Download ${esc(p.original_filename || 'File')}
          </a>
        </div>
      `;
    } else {
      modalFileLinkContainer.innerHTML = `<span style="font-size:.82rem;color:var(--mute)">No document attached</span>`;
    }

    const meds = p.medicines || [];
    const medsNamesSummary = meds.length > 0 ? meds.map(m => esc(m.medicine_name)).join(", ") : "None recorded";
    const medsDosageSummary = meds.length > 0 ? meds.map(m => `${esc(m.medicine_name)}: ${esc(m.dosage || 'Standard')}`).join("; ") : "None recorded";

    detailModalBody.innerHTML = `
      <!-- Priority Structured Fields (1 to 5) -->
      <table class="structured-summary-table">
        <tbody>
          ${p.title ? `
          <tr class="highlight-row">
            <th>Prescription Title</th>
            <td><strong style="color:var(--aqua)">${esc(p.title)}</strong></td>
          </tr>` : ''}
          <tr class="highlight-row">
            <th>1. Date</th>
            <td><strong>${formatDate(p.prescription_date || p.created_at)}</strong></td>
          </tr>
          <tr class="highlight-row">
            <th>2. Main Health Problem</th>
            <td><strong>${esc(p.main_health_problem || p.diagnosis || "Not specified")}</strong></td>
          </tr>
          <tr class="highlight-row">
            <th>3. Medicine Used</th>
            <td><strong>${medsNamesSummary}</strong></td>
          </tr>
          <tr class="highlight-row">
            <th>4. Doctor Name</th>
            <td><strong>${esc(p.doctor_name || "Doctor unspecified")}</strong></td>
          </tr>
          <tr class="highlight-row">
            <th>5. Dosage of Medicine</th>
            <td><strong>${medsDosageSummary}</strong></td>
          </tr>
          <tr>
            <th>Hospital / Clinic</th>
            <td>${esc(p.hospital_name || "Not specified")}</td>
          </tr>
          <tr>
            <th>Clinical Diagnosis</th>
            <td>${esc(p.diagnosis || "Not specified")}</td>
          </tr>
          <tr>
            <th>Doctor Instructions / Notes</th>
            <td>${esc(p.notes || "No additional instructions")}</td>
          </tr>
        </tbody>
      </table>

      <!-- Edit Prescription Information Inline Section -->
      <div id="inline-edit-fields-box" style="display:${isEditingDetails ? 'block' : 'none'};margin-bottom:1.6rem;padding:1.2rem;border-radius:12px;background:rgba(14,24,46,.7);border:1px solid rgba(94,224,208,.3)">
        <h4 style="margin:0 0 1rem;color:var(--aqua)">Edit Prescription Information</h4>
        <div class="vault-fields-grid" style="margin-top:0">
          <div class="vault-field-group">
            <label>Prescription Title</label>
            <input type="text" id="edit-presc-title" value="${esc(p.title || '')}" placeholder="Prescription Title">
          </div>
          <div class="vault-field-group">
            <label>Prescription Date</label>
            <input type="date" id="edit-presc-date" value="${p.prescription_date ? p.prescription_date.split('T')[0] : ''}">
          </div>
          <div class="vault-field-group">
            <label>Main Health Problem</label>
            <input type="text" id="edit-presc-problem" value="${esc(p.main_health_problem || '')}">
          </div>
          <div class="vault-field-group">
            <label>Doctor Name</label>
            <input type="text" id="edit-presc-doctor" value="${esc(p.doctor_name || '')}">
          </div>
          <div class="vault-field-group">
            <label>Hospital or Clinic</label>
            <input type="text" id="edit-presc-hospital" value="${esc(p.hospital_name || '')}">
          </div>
          <div class="vault-field-group">
            <label>Clinical Diagnosis</label>
            <input type="text" id="edit-presc-diagnosis" value="${esc(p.diagnosis || '')}">
          </div>
          <div class="vault-field-group">
            <label>Notes / Instructions</label>
            <input type="text" id="edit-presc-notes" value="${esc(p.notes || '')}">
          </div>
        </div>
        <div style="display:flex;justify-content:flex-end;gap:.6rem;margin-top:1rem">
          <button type="button" class="btn btn-sm" id="cancel-edit-details-btn">Cancel</button>
          <button type="button" class="btn btn-sm p" id="save-edit-details-btn">Save Changes</button>
        </div>
      </div>

      <!-- Prescribed Medicines Structured Sub-Collection -->
      <div style="margin-top:1.6rem">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.8rem;flex-wrap:wrap;gap:.5rem">
          <div>
            <h4 style="margin:0;font-size:1.05rem;color:var(--aqua)">Prescription Medicines (${meds.length})</h4>
            <p style="margin:0;font-size:.82rem;color:var(--mute)">Structured medicines prescribed under this document.</p>
          </div>
          <button type="button" class="btn btn-sm" id="modal-add-med-btn">+ Add Medicine</button>
        </div>

        <!-- Add Medicine Inline Row (Hidden by default) -->
        <div id="modal-new-med-box" style="display:none;margin-bottom:1rem;padding:1rem;border-radius:12px;background:rgba(255,255,255,.05);border:1px solid var(--edge)">
          <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:.6rem">
            <input type="text" id="modal-new-med-name" placeholder="Medicine Name *" required style="font-size:.85rem;padding:.5rem;border-radius:8px;border:1px solid var(--edge);background:#081022;color:var(--text)">
            <input type="text" id="modal-new-med-dosage" placeholder="Dosage (e.g. 10mg)" style="font-size:.85rem;padding:.5rem;border-radius:8px;border:1px solid var(--edge);background:#081022;color:var(--text)">
            <input type="text" id="modal-new-med-freq" placeholder="Frequency (e.g. 1/day)" style="font-size:.85rem;padding:.5rem;border-radius:8px;border:1px solid var(--edge);background:#081022;color:var(--text)">
            <input type="text" id="modal-new-med-dur" placeholder="Duration (e.g. 15 days)" style="font-size:.85rem;padding:.5rem;border-radius:8px;border:1px solid var(--edge);background:#081022;color:var(--text)">
            <input type="text" id="modal-new-med-inst" placeholder="Instructions" style="font-size:.85rem;padding:.5rem;border-radius:8px;border:1px solid var(--edge);background:#081022;color:var(--text)">
          </div>
          <div style="display:flex;justify-content:flex-end;gap:.5rem;margin-top:.8rem">
            <button type="button" class="btn btn-sm" id="cancel-new-med-btn">Cancel</button>
            <button type="button" class="btn btn-sm p" id="confirm-new-med-btn">Add to Prescription</button>
          </div>
        </div>

        ${meds.length > 0 ? `
          <div style="overflow-x:auto">
            <table class="meds-detail-table">
              <thead>
                <tr>
                  <th>Medicine</th>
                  <th>Dosage</th>
                  <th>Frequency</th>
                  <th>Duration</th>
                  <th>Instructions</th>
                  <th style="text-align:right">Actions</th>
                </tr>
              </thead>
              <tbody>
                ${meds.map(m => `
                  <tr id="med-table-row-${m.id}">
                    <td><strong>${esc(m.medicine_name)}</strong></td>
                    <td>${esc(m.dosage || '—')}</td>
                    <td>${esc(m.frequency || '—')}</td>
                    <td>${esc(m.duration || '—')}</td>
                    <td>${esc(m.instructions || '—')}</td>
                    <td style="text-align:right;white-space:nowrap">
                      <button type="button" class="btn btn-sm btn-edit-med" data-medid="${m.id}" title="Edit medicine">✏️</button>
                      <button type="button" class="btn btn-sm btn-danger btn-del-med" data-medid="${m.id}" title="Delete medicine">&times;</button>
                    </td>
                  </tr>
                `).join("")}
              </tbody>
            </table>
          </div>
        ` : `
          <p style="font-size:.9rem;color:var(--mute);padding:.6rem 0">No individual medicines cataloged. Click '+ Add Medicine' to record prescribed items.</p>
        `}
      </div>
    `;

    // Bind Edit Details Toggle
    modalEditToggleBtn.onclick = () => {
      const box = document.getElementById("inline-edit-fields-box");
      isEditingDetails = !isEditingDetails;
      box.style.display = isEditingDetails ? "block" : "none";
      modalEditToggleBtn.textContent = isEditingDetails ? "Hide Edit Form" : "Edit Details";
    };

    const cancelEditBtn = document.getElementById("cancel-edit-details-btn");
    if (cancelEditBtn) {
      cancelEditBtn.onclick = () => {
        isEditingDetails = false;
        document.getElementById("inline-edit-fields-box").style.display = "none";
        modalEditToggleBtn.textContent = "Edit Details";
      };
    }

    const saveEditBtn = document.getElementById("save-edit-details-btn");
    if (saveEditBtn) {
      saveEditBtn.onclick = async () => {
        saveEditBtn.disabled = true;
        saveEditBtn.textContent = "Saving...";
        try {
          const updatedData = {
            title: document.getElementById("edit-presc-title") ? document.getElementById("edit-presc-title").value.trim() || null : null,
            prescription_date: document.getElementById("edit-presc-date").value || null,
            main_health_problem: document.getElementById("edit-presc-problem").value.trim() || null,
            doctor_name: document.getElementById("edit-presc-doctor").value.trim() || null,
            hospital_name: document.getElementById("edit-presc-hospital").value.trim() || null,
            diagnosis: document.getElementById("edit-presc-diagnosis").value.trim() || null,
            notes: document.getElementById("edit-presc-notes").value.trim() || null
          };
          const updated = await prescriptions.update(p.id, updatedData);
          currentDetailPrescription = updated;
          showToast("Prescription details updated!", "success");
          renderPrescriptionDetailsView(updated);
          loadPrescriptionsCollection();
        } catch (err) {
          showToast(err.message || "Failed to update prescription details", "error");
          saveEditBtn.disabled = false;
          saveEditBtn.textContent = "Save Changes";
        }
      };
    }

    // Bind Add Medicine button
    const modalAddMedBtn = document.getElementById("modal-add-med-btn");
    const modalNewMedBox = document.getElementById("modal-new-med-box");
    if (modalAddMedBtn && modalNewMedBox) {
      modalAddMedBtn.onclick = () => {
        modalNewMedBox.style.display = modalNewMedBox.style.display === "none" ? "block" : "none";
        if (modalNewMedBox.style.display === "block") {
          document.getElementById("modal-new-med-name").focus();
        }
      };
    }

    const cancelNewMedBtn = document.getElementById("cancel-new-med-btn");
    if (cancelNewMedBtn && modalNewMedBox) {
      cancelNewMedBtn.onclick = () => {
        modalNewMedBox.style.display = "none";
      };
    }

    const confirmNewMedBtn = document.getElementById("confirm-new-med-btn");
    if (confirmNewMedBtn) {
      confirmNewMedBtn.onclick = async () => {
        const medName = document.getElementById("modal-new-med-name").value.trim();
        if (!medName) {
          showToast("Please enter a medicine name", "error");
          return;
        }

        confirmNewMedBtn.disabled = true;
        try {
          const medPayload = {
            medicine_name: medName,
            dosage: document.getElementById("modal-new-med-dosage").value.trim() || null,
            frequency: document.getElementById("modal-new-med-freq").value.trim() || null,
            duration: document.getElementById("modal-new-med-dur").value.trim() || null,
            instructions: document.getElementById("modal-new-med-inst").value.trim() || null
          };

          await prescriptions.addMedicine(p.id, medPayload);
          showToast(`Added ${medName} to prescription`, "success");
          const refreshed = await prescriptions.get(p.id);
          renderPrescriptionDetailsView(refreshed);
          loadPrescriptionsCollection();
        } catch (err) {
          showToast(err.message || "Failed to add medicine", "error");
          confirmNewMedBtn.disabled = false;
        }
      };
    }

    // Bind Medicine Delete buttons
    detailModalBody.querySelectorAll(".btn-del-med").forEach((btn) => {
      btn.onclick = async () => {
        const medId = btn.dataset.medid;
        if (confirm("Remove this medicine from the prescription?")) {
          btn.disabled = true;
          try {
            await prescriptions.deleteMedicine(p.id, medId);
            showToast("Medicine removed.", "info");
            const refreshed = await prescriptions.get(p.id);
            renderPrescriptionDetailsView(refreshed);
            loadPrescriptionsCollection();
          } catch (err) {
            showToast(err.message || "Failed to delete medicine", "error");
            btn.disabled = false;
          }
        }
      };
    });

    // Bind Medicine Inline Edit buttons
    detailModalBody.querySelectorAll(".btn-edit-med").forEach((btn) => {
      btn.onclick = () => {
        const medId = parseInt(btn.dataset.medid, 10);
        const med = meds.find(m => m.id === medId);
        if (!med) return;

        const row = document.getElementById(`med-table-row-${medId}`);
        if (!row) return;

        row.innerHTML = `
          <td><input type="text" id="row-edit-name-${medId}" value="${esc(med.medicine_name)}" style="font-size:.85rem;padding:.3rem .5rem;border-radius:6px;border:1px solid var(--aqua);background:#081022;color:var(--text);width:100%"></td>
          <td><input type="text" id="row-edit-dosage-${medId}" value="${esc(med.dosage || '')}" style="font-size:.85rem;padding:.3rem .5rem;border-radius:6px;border:1px solid var(--edge);background:#081022;color:var(--text);width:100%"></td>
          <td><input type="text" id="row-edit-freq-${medId}" value="${esc(med.frequency || '')}" style="font-size:.85rem;padding:.3rem .5rem;border-radius:6px;border:1px solid var(--edge);background:#081022;color:var(--text);width:100%"></td>
          <td><input type="text" id="row-edit-dur-${medId}" value="${esc(med.duration || '')}" style="font-size:.85rem;padding:.3rem .5rem;border-radius:6px;border:1px solid var(--edge);background:#081022;color:var(--text);width:100%"></td>
          <td><input type="text" id="row-edit-inst-${medId}" value="${esc(med.instructions || '')}" style="font-size:.85rem;padding:.3rem .5rem;border-radius:6px;border:1px solid var(--edge);background:#081022;color:var(--text);width:100%"></td>
          <td style="text-align:right;white-space:nowrap">
            <button type="button" class="btn btn-sm p" id="row-save-btn-${medId}">Save</button>
            <button type="button" class="btn btn-sm" id="row-cancel-btn-${medId}">Cancel</button>
          </td>
        `;

        document.getElementById(`row-cancel-btn-${medId}`).onclick = () => {
          renderPrescriptionDetailsView(p);
        };

        document.getElementById(`row-save-btn-${medId}`).onclick = async () => {
          const newName = document.getElementById(`row-edit-name-${medId}`).value.trim();
          if (!newName) {
            showToast("Medicine name cannot be empty", "error");
            return;
          }

          try {
            await prescriptions.updateMedicine(p.id, medId, {
              medicine_name: newName,
              dosage: document.getElementById(`row-edit-dosage-${medId}`).value.trim() || null,
              frequency: document.getElementById(`row-edit-freq-${medId}`).value.trim() || null,
              duration: document.getElementById(`row-edit-dur-${medId}`).value.trim() || null,
              instructions: document.getElementById(`row-edit-inst-${medId}`).value.trim() || null
            });
            showToast("Medicine updated", "success");
            const refreshed = await prescriptions.get(p.id);
            renderPrescriptionDetailsView(refreshed);
            loadPrescriptionsCollection();
          } catch (err) {
            showToast(err.message || "Failed to update medicine", "error");
          }
        };
      };
    });

    // Bind Delete Prescription from Modal
    modalDeletePrescBtn.onclick = () => {
      detailModal.classList.remove("active");
      promptDeletePrescription(p.id);
    };
  }

  // Modal Close Handlers
  if (closeDetailModalBtn) {
    closeDetailModalBtn.onclick = () => detailModal.classList.remove("active");
  }
  if (modalCloseBtn) {
    modalCloseBtn.onclick = () => detailModal.classList.remove("active");
  }
  if (detailModal) {
    detailModal.addEventListener("click", (e) => {
      if (e.target === detailModal) detailModal.classList.remove("active");
    });
  }

  // ============================================================
  // CONFIRM DELETE PRESCRIPTION MODAL
  // ============================================================
  function promptDeletePrescription(id) {
    activePrescriptionIdToDelete = id;
    confirmDeleteModal.classList.add("active");
  }

  function closeDeleteModal() {
    activePrescriptionIdToDelete = null;
    confirmDeleteModal.classList.remove("active");
  }

  if (cancelDeleteModalBtn) cancelDeleteModalBtn.onclick = closeDeleteModal;
  if (abortDeleteBtn) abortDeleteBtn.onclick = closeDeleteModal;
  if (confirmDeleteModal) {
    confirmDeleteModal.addEventListener("click", (e) => {
      if (e.target === confirmDeleteModal) closeDeleteModal();
    });
  }

  if (executeDeleteBtn) {
    executeDeleteBtn.onclick = async () => {
      if (!activePrescriptionIdToDelete) return;
      executeDeleteBtn.disabled = true;
      executeDeleteBtn.textContent = "Deleting...";

      try {
        await prescriptions.delete(activePrescriptionIdToDelete);
        showToast("Prescription permanently removed from vault.", "info");
        closeDeleteModal();
        await loadPrescriptionsCollection();
      } catch (err) {
        showToast(err.message || "Failed to delete prescription", "error");
      } finally {
        executeDeleteBtn.disabled = false;
        executeDeleteBtn.textContent = "Yes, Delete";
      }
    };
  }

  // Keyboard accessibility
  window.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      if (cameraModal && (cameraModal.classList.contains("active") || cameraModal.style.display !== "none")) {
        closeCameraModal();
      }
      if (detailModal && detailModal.classList.contains("active")) {
        detailModal.classList.remove("active");
      }
      if (confirmDeleteModal && confirmDeleteModal.classList.contains("active")) {
        closeDeleteModal();
      }
    }
  });

  // ============================================================
  // INITIALIZATION & LIFECYCLE
  // ============================================================
  window.addEventListener("hr:auth_changed", loadPrescriptionsCollection);

  document.addEventListener("DOMContentLoaded", () => {
    // Set default date to today
    const dateInput = document.getElementById("vault-date");
    if (dateInput && !dateInput.value) {
      dateInput.value = new Date().toISOString().split("T")[0];
    }

    loadPrescriptionsCollection();
  });
})();
