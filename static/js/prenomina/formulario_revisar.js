document.addEventListener("DOMContentLoaded", function() {
    /**función async await para verificar las incidencias por rango*/
    async function verificarIncidencias(id){
        var formData = new FormData(document.getElementById("incidencias-form"));
        var costo = parseInt(id)

        try {
            var response = await fetch(`/prenomina/registrar_rango_incidencias/${costo}/`,{
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                },
                body: formData
            });

            var data = await response.json();
            //console.log ("esta es la data: ",data)
            //console.log ("este es el response: ",response)

            if (response.ok) {
                Swal.fire({
                    title: "Mensaje",
                    text: "Se ha agregado la incidencia correctamente",
                    icon: "success",
                    confirmButtonText: "Pulsa aquí para continuar"
                }).then((result) => {
                    if (result.isConfirmed) {
                        window.location.reload();
                    }
                });

                if (data.success) {
                    console.log(data.message); // Mensaje de éxito
                } else {
                    console.error('Error de validación:', data.errors);
                    mostrarErrores(data.errors); // Mostrar errores de validación
                }
            } else {
               
                switch (response.status) {
                    case 405:
                        Swal.fire({
                            title: "Error",
                            text: "No se pudo procesar la solicitud",
                            icon: "warning",
                        })
                        break;
                    case 422:
                        if (data.poscondicion){
                            Swal.fire({
                                title: "Error",
                                text: data.poscondicion,
                                icon: "warning",
                            })
                        }else{
                            if(data.validaciones){
                                //console.log(data.errores)
                                Swal.fire({
                                    title: "Error",
                                    text: data.validaciones,
                                    icon: "warning",
                                })
                            }
                            
                        }
                        break;
                    default:
                        console.log('Mensaje no reconocido');
                }
                //console.log(response)
                //console.error('Error en la respuesta del servidor:', response.status);
            }



        } catch (error) {
            Swal.fire({
                title: "Error",
                text: "No se pudo procesar la solicitud",
                icon: "warning",
            })
        }
    }    

     //Clic al botón de guardar la incidencia por rango
     var boton_programar = document.getElementById("btn-programar")
     boton_programar.addEventListener("click", function(e) {
         e.preventDefault();
         //se obtiene el valor del id del input hidden costo  
         var costo = document.getElementById('costo-id').value 
         console.log(costo)
         //se llama la función
         verificarIncidencias(costo)
     });




    //para deshabilitar las incidencias de cada formulario revisar
    for (i = 0; i < 14; i++){
        var select = document.getElementById("id_form-"+i+"-incidencia")
        //se enumeran y empieza con 1 en la lista del despegable
        select.options[2].disabled = true
        select.options[3].disabled = true
        //select.options[7].disabled = true
        select.options[9].disabled = true
        select.options[11].disabled = true
        select.options[12].disabled = true
        select.options[13].disabled = true
        select.options[14].disabled = true
        select.options[15].disabled = true
        //select.options[17].disabled = true
      
    }

    //desmarcar las incidencias para que posteriormente se guarden, eliminen correctamente
    var botonGuardar = document.getElementById('guardar')
    botonGuardar.addEventListener('click',function(){
        for (i = 0; i < 14; i++){
            var select = document.getElementById("id_form-"+i+"-incidencia")
            select.options[2].disabled = false
            select.options[3].disabled = false
            //select.options[7].disabled = false
            select.options[9].disabled = false
            select.options[11].disabled = false
            select.options[12].disabled = false
            select.options[13].disabled = false
            select.options[14].disabled = false
            select.options[15].disabled = false
            //select.options[17].disabled = false
        }
    })
    
    //Activar boton eliminar y guardar - checkbox
    var checkboxes = document.querySelectorAll('input[type="checkbox"]');

    function verificarAlMenosUnoActivo() {
        for (var i = 0; i < checkboxes.length; i++) {
            if (checkboxes[i].checked) {
                return true; // Retorna true si encuentra al menos uno activo
            }
        }
        return false; // Retorna false si ninguno está activo
    }

    for (var i = 0; i < checkboxes.length; i++) {
        checkboxes[i].addEventListener('change', function() {
            botonGuardar = document.getElementById('guardar')
            if (verificarAlMenosUnoActivo()) {
                //activa eliminar
                botonGuardar.classList.remove('btn-primary')
                botonGuardar.classList.add('btn-danger')
                botonGuardar.textContent = "Eliminar"
                botonGuardar.setAttribute('name', 'eliminar_cambios');
            } else {
                //activa guardar
                botonGuardar.classList.remove('btn-danger')
                botonGuardar.classList.add('btn-primary')
                botonGuardar.textContent = "Guardar"
                botonGuardar.setAttribute('name', 'guardar_cambios');
            }
        });
    }



    //formulario rango incidencia - ocultar subsecuente
    var formRangoSelect = document.getElementById('id_incidencia');
    var subsecuente = document.getElementById('id-subsecuente');

    var inciedencia = document.getElementById('id_incidencia')
    var dia_inhabil = document.getElementById('id_dia_inhabil')
    var display_dia_inhabil = document.getElementById('id-display-dia-inhabil')


    formRangoSelect.addEventListener('change', function() {
        var opcion = formRangoSelect.value;

        //solo se activa para cualquuier caso de incapacidad
        if (opcion !== '10' && opcion !== '12' && opcion !== '11') { //cualquier incapacidad
            subsecuente.classList.add('d-none'); //ocultar
        } else {
            subsecuente.classList.remove('d-none'); //mostrar
        }
        
        //para ocultar el dia inhabil y dejar marcado como domingo por defecto
        /*
        if (opcion === '10' || opcion === '12' || opcion === '11') {
            console.log("ocultar el dia inhabil");
            dia_inhabil.value = '7'; // Ajustar el valor del select a '7' (Domingo)
            display_dia_inhabil.classList.add('d-none')
        }else{
            dia_inhabil.value = '';
            display_dia_inhabil.classList.remove('d-none')
        }
        */



    });
    
});