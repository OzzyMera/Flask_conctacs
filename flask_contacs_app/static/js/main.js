const btnDelete = document.querySelectorAll('.btn-delete')

if (btnDelete) {
    const btnarray = Array.from(btnDelete);
    btnarray.forEach((btn) => {
        btn.addEventListener('click', (e) => {
            if (!confirm('Estas seguro de eliminar el contacto')) {
                e.preventDefault();
            }
        });
    });
}