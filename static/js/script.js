const checkbox = document.getElementById('check');
const body = document.body;

checkbox.addEventListener('change', function() {
    if (checkbox.checked) {
        body.style.overflow = 'hidden';
    } else {
        body.style.overflow = 'auto';
    }
});


function readURL(input) {
    if (input.files && input.files[0]) {
    const file = input.files[0];
    const filePreview = document.getElementById('file-preview');
    filePreview.innerHTML = '';

    const fileName = document.createElement('p');
    fileName.textContent = `File Name: ${file.name}`;
    const fileSize = document.createElement('p');
    fileSize.textContent = `File Size: ${file.size} bytes`;
    const fileType = document.createElement('p');
    fileType.textContent = `File Type: ${file.type}`;

    filePreview.appendChild(fileName);
    $('.file-upload').css("width", "fit-content");
    $('.image-upload-wrap').hide();
    $('.file-upload-content').show();
    $('.file-upload-btn').hide();
    }
}

// file-upload-content

function removeTestUpload() {
    const fileInput = document.getElementById('file-upload');
    fileInput.value = '';
    document.getElementById('file-preview').innerHTML = '';
    $('.file-upload-btn').show();
    $('.file-upload-content').hide();
}

function upload(){
    $('.overlay').show()
}

function removeUpload() {
    $('.file-upload-input').replaceWith($('.file-upload-input').clone());
    $('.file-upload-btn').show();
    $('.file-upload-content').hide();
    $('.image-upload-wrap').show();
    $('.file-upload').css("width", "600px");

}

$('.image-upload-wrap').bind('dragover', function () {
        $('.image-upload-wrap').addClass('image-dropping');
    });
    $('.image-upload-wrap').bind('dragleave', function () {
        $('.image-upload-wrap').removeClass('image-dropping');
});

