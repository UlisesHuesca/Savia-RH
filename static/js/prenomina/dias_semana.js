document.addEventListener("DOMContentLoaded", function() {
    /*Permite poner los dias de la semana al lado del formulario */
    var filas = document.querySelectorAll('#tabla_incidencias tbody tr');
    var dias_semana = ['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo']
    dias_semana = dias_semana.concat(dias_semana);

    // Iterar sobre cada fila y agregar texto en la primera celda (columna)
    filas.forEach(function(fila,index) {
        var primeraCelda = fila.querySelector('td:first-child');
        dia = dias_semana[index]    
        primeraCelda.textContent = dia
        index++
    });
});