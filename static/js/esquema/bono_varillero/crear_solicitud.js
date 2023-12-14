document.addEventListener("DOMContentLoaded", (e) => {

    /**Mensajes de alerta*/
    function mensajeBonoNa(){
        document.getElementById('cantidad').setAttribute('value','') 
        Swal.fire({
            title: "No aplica",
            text: "Este esquema de bono no aplica, selecciona otro",
            icon: "warning",
        })
    }

    /**Seleccionar esquema bono */
    async function solicitarEsquemaBono(bono,puesto){
        try {
            var response = await fetch('/esquema/solicitar_esquema_bonos/',{
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    'Content-Type': 'application/json',
                },
                body:JSON.stringify({
                    'bono':bono,
                    'puesto':puesto
                }),
            });

            const datos = await response.json();
            cantidad = datos[0].fields.importe
            cantidad === null ? mensajeBonoNa() : document.getElementById('cantidad').setAttribute('value',cantidad) 

        } catch (error) {
            //console.log(error)
            document.getElementById('cantidad').setAttribute('value','') 
            Swal.fire({
                title: "Error",
                text: "No se pudo procesar la solicitud",
                icon: "warning",
            })

        }
    }

    //para cargar la cantidad del bono cuando se seleccione alguno puesto o bono
    var puestoSelect = document.getElementById("puesto");
    var bonoSelect = document.getElementById("bono");

    puestoSelect.addEventListener("change",function (e) {
        const bono = document.getElementById("bono").value;
        const puesto = document.getElementById("puesto").value;

        if(bono.length != 0 && puesto.length != 0){
            solicitarEsquemaBono(bono,puesto)

        }

    });

    bonoSelect.addEventListener("change",function (e) {
        const bono = document.getElementById("bono").value;
        const puesto = document.getElementById("puesto").value;

        if(bono.length != 0 && puesto.length != 0){
            solicitarEsquemaBono(bono,puesto)

        }

    });

    /**Remover bono de la solicitud*/
    async function removerBono(bonoId){
        try {
            var respuesta= await fetch(`/esquema/remover_bono/${bonoId}/`,{
            //var respuesta= await fetch('/esquema/remover_bono/',{
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    'Content-Type': 'application/json',
                },
                body:JSON.stringify({
                    'bonoId':bonoId,
                }),
            });

            const datos = await respuesta.json();
            
            if (respuesta.status === 200) {
                console.log(datos)
                //eliminar la fila
                const renderizar = document.querySelectorAll(`[data-id="${datos.bono_id}"]`)
                renderizar[0].remove()
                //renderizar el total en html
                document.getElementById('total').textContent = datos.total

            }else{
                Swal.fire({
                    title: "Error",
                    text: "No existe este bono en nuestros registros",
                    icon: "warning",
                })
            }

        } catch (error) {
            console.log(error)
            Swal.fire({
                title: "Error",
                text: "No se pudo procesar la solicitud",
                icon: "warning",
            })

        }
    }

    tabla = document.getElementById("tabla")
    if (tabla) {
        addEventListener("click", async function(e){
            //hacer click en el boton eliminar
            if(e.target.classList.contains("btn-danger") || e.target.classList.contains("fa-minus")){
                
                //vericar la clase que contiene para obtener el id del bono
                if (e.target.classList.contains("btn-danger")){
                    elemento = e.target.parentNode.parentNode
                    bonoId = elemento.getAttribute('data-id');
                }else{
                    elemento = e.target.parentNode.parentNode.parentNode
                    bonoId = elemento.getAttribute('data-id');
                }

                //mensaje de confirmacion para eliminar
                if (bonoId > 0){
                    Swal.fire({
                    title: "¿Desea quitar este bono?",
                    text: "No se puede deshacer esta acción",
                    icon: "warning",
                    showCancelButton: true,
                    confirmButtonColor: "#3085d6",
                    cancelButtonColor: "#696969",
                    confirmButtonText: "Aceptar",
                    cancelButtonText: "Cancelar"
                  }).then((result) => {
                    if (result.isConfirmed) {
                        removerBono(bonoId)
                    }
                });
                }

            }
        });
    }


    /**Para eliminar un archivo */
    async function removerArchivo(archivo){
        try {
            var response = await fetch(`/esquema/remover_archivo/${archivo}/`,{
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    'Content-Type': 'application/json',
                },
                body:JSON.stringify({
                    'archivo_id':archivo,
                }),
            });
            const datos = await response.json();
            if (response.status === 200){
                console.log(datos)
                var renderizar = document.querySelectorAll(`[data-archivo="${datos.archivo_id}"]`)
                renderizar[0].remove()
            }else{
                Swal.fire({
                    title: "Error",
                    text: "No se encontro el recurso solicitado",
                    icon: "warning",
                })
            }
        } catch (error) {
            console.log(error)
            Swal.fire({
                title: "Error",
                text: "No se pudo procesar la solicitud",
                icon: "warning",
            })
        }
    }

    files = document.getElementById("archivos")
    if (files) {
        addEventListener("click", async function(e){
            if(e.target.classList.contains('small')){
                archivo_id = e.target.getAttribute("data-archivo")
                console.log("el ID del archivo es: ",archivo_id)
                removerArchivo(archivo_id)

            }
        });
    }

    

});