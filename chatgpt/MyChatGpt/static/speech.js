
          // Check if SpeechRecognition is supported by the browser
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            alert('Speech Recognition is not supported in this browser.');
            return;
        }

        // Create a new instance of SpeechRecognition
        const recognition = new SpeechRecognition();

        // Update the textarea with the recognized words
        recognition.onresult = function(event) {
            const speechTextarea = document.getElementById('userInput');
            const transcript = Array.from(event.results)
                .map(result => result[0])
                .map(result => result.transcript)
                .join('');
            speechTextarea.value = transcript;
        };

        // Handle the microphone icon click event
        document.getElementById('microphone').addEventListener('click', function(e) {
            // Start speech recognition
            recognition.start();
            e.preventDefault()
            return false
        });
    });