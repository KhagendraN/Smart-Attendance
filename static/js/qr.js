function generateQR(classId) {
    fetch(`/generate_qr/${classId}`)
        .then(response => response.json())
        .then(data => {
            const qrModal = new bootstrap.Modal(document.getElementById('qrModal'));
            document.getElementById('qrImage').src = `data:image/png;base64,${data.qr_code}`;
            qrModal.show();
        })
        .catch(error => console.error('Error generating QR code:', error));
}
