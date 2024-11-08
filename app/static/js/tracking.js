var audioElement = document.getElementById('radio-player');
var startTime;

  // If the audio is already playing, trigger the play event manually
if (!audioElement.paused) {
  startTime = Date.now();
  gtag('event', 'play_stream', {
    'event_category': 'Radio Player',
    'event_label': 'Stream Play'
  });
}

// Event listener for play
audioElement.addEventListener('play', function() {
  startTime = Date.now(); // Store the start time when the user presses play
  gtag('event', 'play_stream', {
    'event_category': 'Radio Player',
    'event_label': 'Stream Play'
  });
});

// Event listener for pause or stop
audioElement.addEventListener('pause', function() {
  var endTime = Date.now(); // Get the time when the stream is paused
  var duration = Math.floor((endTime - startTime) / 1000); // Calculate the duration in seconds
  
  gtag('event', 'stop_stream', {
    'event_category': 'Radio Player',
    'event_label': 'Stream Pause',
    'event_value': duration, // Send the listening duration to GA4
    'listening_duration': duration // Custom parameter for duration
  });
});

// Optional: Event listener for when the user closes or leaves the page
window.addEventListener('beforeunload', function() {
  if (!audioElement.paused) { // Check if the stream is still playing
    var endTime = Date.now();
    var duration = Math.floor((endTime - startTime) / 1000);
    
    gtag('event', 'stop_stream', {
      'event_category': 'Radio Player',
      'event_label': 'Stream Stop (Page Exit)',
      'event_value': duration
    });
  }
});
