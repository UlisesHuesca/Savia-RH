document.addEventListener('DOMContentLoaded', function(e) {
    /**Eliminar una solicitud con la cantidad de bonos seleccionados y sus imagenes*/
    async function eliminarSolicitud(solicitudId){
        try {
            var response = await fetch(`/esquema/eliminar_solicitud/${solicitudId}/`,{
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    'Content-Type': 'application/json',
                },
                body:JSON.stringify({
                    'solicitudId':solicitudId,
                }),
            });
            const datos = await response.json();
            console.log(datos)
            if (response.status === 200) {
                const renderizar = document.querySelectorAll(`[data-solicitud="${datos.solicitud}"]`)
                renderizar[0].remove()
                Swal.fire({
                    title: "Eliminado",
                    text: "La solicitud se elimino correctamente",
                    icon: "success"
                });
            }

        } catch (error) {
            console.log(error)
            Swal.fire({
                title: "Error",
                text: "No existe esta solicitud en nuestros registros",
                icon: "warning",
            })
        }
    }

    tabla = document.getElementById('tabla')

    tabla.addEventListener('click',async function(e){
         //hacer click en el boton eliminar
         if(e.target.classList.contains('btn-rojo') || e.target.classList.contains('fa-trash-alt')){
            //verficar la clase que contiene para obtener el id de la solicitud
            if (e.target.classList.contains("btn-rojo")){
                elemento = e.target.parentNode.parentNode
                solicitudId = elemento.getAttribute('data-solicitud');
            }else{
                elemento = e.target.parentNode.parentNode.parentNode
                solicitudId = elemento.getAttribute('data-solicitud');
            }

            //mensaje de confirmacion para eliminar
            if (solicitudId > 0) {
                Swal.fire({
                    title: "¿Desea eliminar esta solicitud?",
                    text: "No se puede deshacer esta acción",
                    icon: "warning",
                    showCancelButton: true,
                    confirmButtonColor: "#3085d6",
                    cancelButtonColor: "#696969",
                    confirmButtonText: "Aceptar",
                    cancelButtonText: "Cancelar"
                }).then((result) => {
                    if (result.isConfirmed) {
                        //console.log(solicitudId)
                        eliminarSolicitud(solicitudId)
                    }
                });
            }
        }
    });



});