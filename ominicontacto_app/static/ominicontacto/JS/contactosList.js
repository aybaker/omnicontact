$(document).ready(function(){

  var $inputContacto = $('#pk_contacto');
  var pk_campana = $('#pk_campana').attr('value');

  function create_node (type, attrs) {
    var $node = $("<" + type + "/>", attrs);
    return $node;
  }

  function obtener_nodos_acciones (row, data, index) {
    var pk_contacto = data[0];

    var $modificar_contacto = create_node('a', {
          'href': '/contacto/'+ pk_contacto + '/update/',
        });
        var $span_modificar_contacto = create_node('span', {
          'class': 'glyphicon glyphicon-tasks',
          'aria-hidden': 'true',
          'title': 'Modificar',
        });
    $modificar_contacto.append($span_modificar_contacto);

    var $llamar_contacto = create_node('button', {
          'class': 'contacto-lista btn btn-link',
        });
    var $span_llamar_contacto = create_node('span', {
          'class': 'glyphicon glyphicon-earphone',
          'aria-hidden': 'true',
          'title': 'Llamar',
        });
    $llamar_contacto.append($span_llamar_contacto);
    $llamar_contacto
          .on('click', function() {
            $inputContacto.attr('value', pk_contacto);
            $('#lista_llamar_contacto').trigger('click');
          });

    var $mailto_contacto = create_node('a', {
          'href': '#',
        });
    var $span_mailto_contacto = create_node('span', {
          'class': 'glyphicon glyphicon-envelope',
          'aria-hidden': 'true',
          'title': 'Email',
        });
    $mailto_contacto.append($span_mailto_contacto);

    return [$modificar_contacto, $llamar_contacto, $mailto_contacto];
  }

  $('#agenteContactosTable')
    .DataTable( {
      // Convierte a datatable la tabla de contactos
      "createdRow": function ( row, data, index ) {
        nodo_acciones = obtener_nodos_acciones(row, data, index);
        $(row).find('td').last().append(nodo_acciones);
      },
      serverSide: true,
      processing: true,
      ajax: '/api/campana/' + pk_campana + '/contactos/',
      ordering: false,
      paging: true,
      language: {
        search: "Buscar: ",
        infoFiltered:"(filtrando de un total de _MAX_ contactos)",
        paginate: {
          first: "Primero ",
          previous: "Anterior ",
          next: " Siguiente",
          last: " Último"
        },
        lengthMenu: "Mostrar _MENU_ entradas",
        info: "Mostrando _START_ a _END_ de _TOTAL_ entradas",
      }
    });
});