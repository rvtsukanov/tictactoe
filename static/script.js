(function(window, document, undefined){

window.onload = init;
var socket = io();

function init(){
    var sid = socket.id

   socket.on('connect', function() {
       console.log('Connected!')
       socket.emit('connection_established',
           {'socket_context': {'whoami': socket.id}, 'game_context': {}, 'extra': {}});
           // {'whoami': socket.id});
       sid = socket.id
   });

    socket.on('disconnect', function (data){
        console.log('socket is disconnected!', socket.id)
        socket.emit('disconnect', {'socket_context': {'whoami': socket.id}, 'game_context': {}, 'extra': {}})
    })

   socket.on('step_proceeded', function(data){
       const new_body = data['game_context']['deck_body']

       var elem = document.getElementById('body')
       elem.innerHTML = new_body

       console.log('data, step', data)

       var console_div = document.getElementById('console')
       console_div.innerText = 'Console: ' + data["game_context"]["console_message"]

       var players_num_div = document.getElementById('players_num')
       players_num_div.innerText = 'Player num: ' + data["socket_context"]["num_players"]

       var ismineturn_div = document.getElementById('ismineturn')
       console.log('turn', data["game_context"]["last_turn_by"], socket.id)
       ismineturn_div.innerText = 'Your turn: ' + data["game_context"]["last_turn_by"] == socket.id

       var whoami_div = document.getElementById('whoami')
       whoami_div.innerText = socket.id

       console.log(document.innerHTML)

       for(i = 0; i < cell.length; i++){
         console.log(cell[i].id)
      cell[i].onclick = function() {
        socket.emit('button_click',
            {'socket_context': {'whoami': socket.id,
                'button_id': this.id}, 'game_context': {}, 'extra': {}}
                );
      }
  }
   });

   socket.on('connection_established', function(data){
            // console.log('Obtain auth data', Object.keys(data))
       var elem = document.getElementById('body')
       const new_body = data['game_context']['deck_body']

       elem.innerHTML = new_body

       console.log('data, conn est', data)

       var console_div = document.getElementById('console')
       console_div.innerText = 'Console: ' + data["game_context"]["console_message"]

       var players_num_div = document.getElementById('players_num')
       players_num_div.innerText = 'Player num: ' + data["socket_context"]["num_players"]

       var ismineturn_div = document.getElementById('ismineturn')
       console.log('turn', data["game_context"]["last_turn_by"], socket.id)
       ismineturn_div.innerText = 'Your turn: ' + data["game_context"]["last_turn_by"] == socket.id

       var whoami_div = document.getElementById('whoami')
       whoami_div.innerText = socket.id


       for(i = 0; i < cell.length; i++){
         console.log(cell[i].id)
      cell[i].onclick = function() {
        console.log(111)
        socket.emit('button_click',
            // {'whoami': sid, 'button_id': this.id}

            {'socket_context': {'whoami': socket.id,
                'button_id': this.id}, 'game_context': {}, 'extra': {}}

            );
      }
  }
   });

  var cell = document.getElementsByClassName('divTableCell');


  }

})(window, document, undefined);
