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

    /**Registro de la solicitud */
    async function agregarBonoSolicitud(folio,bono,empleado,puesto,cantidad){
        try {
            var response = await fetch('/esquema/bonos_varillero/crear_solicitud/',{
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    'Content-Type': 'application/json',
                },
                body:JSON.stringify({
                    'folio':folio,
                    'bono':bono,
                    'empleado':empleado,
                    'puesto':puesto,
                    'cantidad':cantidad
                }),
            });

            const datos = await response.json();
            console.log(datos)
            


        } catch (error) {
            console.log(error)
            document.getElementById('cantidad').value = ''
            Swal.fire({
                title: "Error",
                text: "No se pudo procesar la solicitud",
                icon: "warning",
            })

        }
    }

    var agregar = document.getElementById("btnAgregar")
    agregar.addEventListener("click",function (e) {
        e.preventDefault()

        folio = document.getElementById('folio').value
        bono = document.getElementById('bono').value
        empleado = document.getElementById('empleado').value
        puesto = document.getElementById('puesto').value
        cantidad = document.getElementById('cantidad').value

        //console.log(bono,empleado,puesto,cantidad)

        agregarBonoSolicitud(folio,bono,empleado,puesto,cantidad)

    });

   


});