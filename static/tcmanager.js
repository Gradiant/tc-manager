
var current_interface;

function validate_ip(input_text)
{
   var ip_format = /^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
   return input_text.match(ip_format)
}

function add_event_handlers() {
    $('body').on('click','#rate_remove', function(){
               console.log("rate_remove");
               //$('#confirm').show();
                $( "#confirm" ).attr('title', 'Delete default rate');
                $( "#confirm > .message").html('');
                $( "#confirm" ).dialog({
                      resizable: false,
                      height: "auto",
                      width: 480,
                      modal: true,
                      buttons: {
                        "current interface": function() {
                             $.ajax({
                                url: "/api/interfaces/"+current_interface+"/default_rate",
                                type: 'DELETE',
                                contentType: 'application/json',
                                timeout: 1000
                                }).done(function() {
                                       console.log('updated');
                                       show_interface_info(current_interface);
                                       });
                                $( this ).dialog( "close" );
                        },
                        "All interfaces": function() {
                             $.ajax({
                                url: "/api/interfaces/default_rate",
                                type: 'DELETE',
                                contentType: 'application/json',
                                timeout: 1000
                                }).done(function() {
                                       console.log('updated');
                                       show_interface_info(current_interface);
                                       });
                                $( this ).dialog( "close" );
                        },
                        Cancel: function() {
                          $( this ).dialog( "close" );
                        }
                      }
                    });
               });

    $('body').on('click','#rate_edit', function(){
               console.log("rate_edit");
                $("#confirm").attr('title', 'Edit default rate');
                 $( "#confirm > .message").html('Default rate: <input type="text" id="rate_input" value="1"><select id="rate_units">'
                                    +'<option value="Mbit" selected="selected">Mbps</option>'
                                    +'<option value="Kbit">kbps</option></select>')
                $( "#confirm" ).dialog({
                      resizable: false,
                      height: "auto",
                      width: 480,
                      modal: true,
                      buttons: {
                        "current interface": function() {
                             rate = $('#confirm > .message > #rate_input').val()+$('#confirm > .message > #rate_units').val();
                                console.log(rate)
                                $.ajax({
                                    url: "/api/interfaces/"+current_interface+"/default_rate",
                                    type: 'PUT',
                                    contentType: 'application/json',
                                    data: JSON.stringify(rate),
                                    timeout: 1000
                                    }).done(function() {
                                       console.log('updated');
                                       show_interface_info(current_interface);
                                       })
                                    .fail(function() {
                                        console.error( "error from server" );
                                     });
                                $( this ).dialog( "close" );
                        },
                        "All interfaces": function() {
                             rate = $('#confirm > .message > #rate_input').val()+$('#confirm > .message > #rate_units').val();
                                console.log(rate)
                                $.ajax({
                                    url: "/api/interfaces/default_rate",
                                    type: 'PUT',
                                    contentType: 'application/json',
                                    data: JSON.stringify(rate),
                                    timeout: 1000
                                    }).done(function() {
                                       console.log('updated');
                                       show_interface_info(current_interface);
                                       })
                                    .fail(function() {
                                        console.error( "error from server" );
                                     });
                                $( this ).dialog( "close" );
                        },
                        Cancel: function() {
                          $( this ).dialog( "close" );
                        }
                      }
                    });
               });

    $('body').on('click','#policy_add', function(){
               console.log("policy_add");
                $("#confirm-policy").attr('title', 'Add Policy');
                $( "#confirm-policy" ).dialog({
                      resizable: false,
                      height: "auto",
                      width: 520,
                      modal: true,
                      buttons: {
                        "current interface": function() {
                                policy = {
                                    action: {
                                       rate: $('#confirm-policy > .message > #rate_input').val()+$('#confirm-policy > .message > #rate_units').val()
                                    },
                                    match: {
                                    }
                                 };

                                if ($('#confirm-policy > .message > #src_ip').val() != '') {
                                       policy.match.src_ip = $('#confirm-policy > .message > #src_ip').val()
                                }
                                if ($('#confirm-policy > .message > #dst_ip').val() != '') {
                                       policy.match.dst_ip = $('#confirm-policy > .message > #dst_ip').val()
                                }
                                if ($('#confirm-policy > .message > #src_port').val() != '') {
                                       policy.match.src_port = $('#confirm-policy > .message > #src_port').val()
                                }
                                if ($('#confirm-policy > .message > #dst_port').val() != '') {
                                       policy.match.dst_port = $('#confirm-policy > .message > #dst_port').val()
                                }
                                console.log(policy)

                                $.ajax({
                                    url: "/api/interfaces/"+current_interface+"/policies",
                                    type: 'POST',
                                    contentType: 'application/json',
                                    data: JSON.stringify(policy),
                                    timeout: 1000
                                    }).done(function() {
                                       console.log('updated');
                                       show_interface_info(current_interface);
                                       })
                                    .fail(function() {
                                        console.error( "error from server" );
                                     });
                                $( this ).dialog( "close" );
                        },
                        "All interfaces": function() {
                                policy = {
                                    action: {
                                       rate: $('#confirm-policy > .message > #rate_input').val()+$('#confirm-policy > .message > #rate_units').val()
                                    },
                                    match: {
                                    }
                                 };

                                if ($('#confirm-policy > .message > #src_ip').val() != '') {
                                       policy.match.src_ip = $('#confirm-policy > .message > #src_ip').val()
                                }
                                if ($('#confirm-policy > .message > #dst_ip').val() != '') {
                                       policy.match.dst_ip = $('#confirm-policy > .message > #dst_ip').val()
                                }
                                if ($('#confirm-policy > .message > #src_port').val() != '') {
                                       policy.match.src_port = $('#confirm-policy > .message > #src_port').val()
                                }
                                if ($('#confirm-policy > .message > #dst_port').val() != '') {
                                       policy.match.dst_port = $('#confirm-policy > .message > #dst_port').val()
                                }
                                console.log(policy)


                                $.ajax({
                                    url: "/api/interfaces/policies",
                                    type: 'POST',
                                    contentType: 'application/json',
                                    data: JSON.stringify(policy),
                                    timeout: 1000
                                    }).done(function() {
                                       console.log('updated');
                                       show_interface_info(current_interface);
                                       })
                                    .fail(function() {
                                        console.error( "error from server" );
                                     });
                                $( this ).dialog( "close" );
                        },
                        Cancel: function() {
                          $( this ).dialog( "close" );
                        }
                      }
                    });
               });
}


function delete_policy(policy_id) {
            $( "#confirm" ).attr('title', 'Delete Policy'+policy_id);
            $( "#confirm > .message").html('');
            $( "#confirm" ).dialog({
                  resizable: false,
                  height: "auto",
                  width: 480,
                  modal: true,
                  buttons: {
                    "current interface": function() {
                      $.ajax({
                         url: "/api/interfaces/"+current_interface+"/policies/"+policy_id,
                        type: 'DELETE',
                         }).done(function() {
                                   console.log('deleted policy');
                                   show_interface_info(current_interface);
                                   });
                            $( this ).dialog( "close" );
                    },
                    //"All interfaces": function() {
                    //  $( this ).dialog( "close" );
                    //},
                    Cancel: function() {
                      $( this ).dialog( "close" );
                    }
                  }
                });
           }

function show_interface_info(interface) {
$('#interface_info').show()
current_interface=interface;
console.log("showing interface "+interface);
 $('#interface_info > h2').text(interface);
 $.ajax({
        url: "/api/interfaces/"+interface
    }).then(
      function(data) {
       data.default_rate = data.default_rate || '-';
       $('#interface_info > .rate > span').text(data.default_rate);
       $('#interface_info').find('tbody').text('');
       data.policies.forEach( policy => {
       policy.match.src_ip = policy.match.src_ip || '-';
       policy.match.dst_ip = policy.match.dst_ip || '-';
       policy.match.src_port = policy.match.src_port || '-';
       policy.match.dst_port = policy.match.dst_port || '-';
       $('#interface_info').find('tbody').append('<tr><td>'
                    +policy.policy_id
                    +'<i class="fa fa-remove" onclick=delete_policy("'
                    +policy.policy_id+'")></i></td>' +
                    '<td>'+policy.match.src_ip+'</td>' +
                    '<td>'+policy.match.src_port+'</td>' +
                    '<td>'+policy.match.dst_ip+'</td>' +
                    '<td>'+policy.match.dst_port+'</td>' +
                    '<td>'+policy.action.rate+'</td></tr>')
       })
       });
 }

$(document).ready(function() {
    console.log("ready")
    add_event_handlers();
    $.ajax({
        url: "/api/interfaces"
    }).then(function(data) {
    data.interfaces.forEach(interface => {
    console.log(interface)
       $('#interfacelist').append("<a>"+interface+"</a>");
       $('#interfacelist').find("a").last().click(function() { show_interface_info(interface)});
     });
     });
});

