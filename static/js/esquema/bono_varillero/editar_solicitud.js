document.addEventListener('DOMContentLoaded', function() {

    cambiarBono = document.getElementById('cambiarBono')

    async function solicitarCambiarBono(folio){
        var response = await fetch(`/esquema/remover_bonos/editar/${folio}/`,{
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'Content-Type': 'application/json',
            },
            body:JSON.stringify({
                'solicitud_id':folio,
            }),
        });

        const datos = await response.json();

        if(response.status === 200){
            var tabla = document.getElementById('tabla');
            tabla.remove()
            Swal.fire({
                title: "Sistema",
                text: "Se han eliminado los bonos",
                icon: "success"
              });
        }else{
            Swal.fire({
                title: "Error",
                text: "No se encontro el recurso solicitado",
                icon: "warning",
            })
        }
    }

    cambiarBono.addEventListener('click', async function(e){
        Swal.fire({
            title: "¿Está seguro de que desea realizar esta acción?",
            text: "Al realizar el cambio, no será posible asociar el tipo de bono, con los bonos solicitados previamente, por lo tanto se eliminarán",
            icon: "warning",
            showCancelButton: true,
            confirmButtonColor: "#3085d6",
            cancelButtonColor: "#696969",
            confirmButtonText: "Aceptar",
            cancelButtonText: "Cancelar"
          }).then((result) => {
            if (result.isConfirmed) {
                var folio = document.querySelector('[name="folio"]').value;
                solicitarCambiarBono(folio)
            }
          });


    })






});