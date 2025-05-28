let currentCard = null;
let score = 0;
let total = 0;

async function loadNewCard() {
    /*
    Load a new random card for guessing. Selects the card, randomly positions it and zooms in.
    */
    const response = await fetch('/api/random-card-art');
    const card = await response.json();
        
    if (!card || !card.image_uri_art_crop) {
        throw new Error('No card art available');
    }

    currentCard = card;
    const img = document.getElementById('cardArt');
    img.src = card.image_uri_art_crop;
        
    // Randomly position the art
    const x = Math.random() * 100;
    const y = Math.random() * 100;
    img.style.objectPosition = `${x}% ${y}%`;
    img.style.objectFit = 'cover';
    img.style.transform = 'scale(1.2)';
    img.style.transformOrigin = 'center';
        
    const feedback = document.getElementById('feedback');
    feedback.textContent = '';
    feedback.className = 'feedback';
        
    const input = document.getElementById('guessInput');
    input.value = '';
    document.getElementById('cardSuggestions').innerHTML = '';
    input.focus();
}

async function submitGuess(event) {
    /*
    When the submit button is pressed, determine if the guess is right and display the results.
    */
    event.preventDefault();
    
    if (!currentCard) return;
    
    const guess = document.getElementById('guessInput').value.toLowerCase().trim();
    const correctName = currentCard.name.toLowerCase();
    const feedback = document.getElementById('feedback');
    
    if (guess === correctName) {
        score++;
        total++;
        document.getElementById('score').textContent = score;
        document.getElementById('total').textContent = total;
        feedback.textContent = 'Correct! Loading next card...';
        feedback.className = 'feedback correct';
        setTimeout(loadNewCard, 500);
    } else {
        total++;
        document.getElementById('total').textContent = total;
        feedback.textContent = `Incorrect! The card was ${currentCard.name}. Loading next card...`;
        feedback.className = 'feedback incorrect';
        setTimeout(loadNewCard, 500);
    }
}

async function updateResults(query, resultList, input, resultBox) {
    /*
    Get the suggestions based on the current input text, fill in when suggestion is clicked.
    */
    const name = query.trim();
    if (name === '') {
        resultBox.style.display = 'none';
        resultList.innerHTML = '';
        return;
    }

    let url = '/api/suggestions?';
    if (name) url += `name=${encodeURIComponent(name)}&`;
    const response = await fetch(url);
    const suggestions = await response.json();

    if (suggestions.length === 0) {
        resultList.innerHTML = '<li>No matches found</li>';
    } else {
        resultList.innerHTML = suggestions.map(item => `<li class="suggestion-item">${item.name}</li>`).join('');
    }

    const items = resultList.querySelectorAll('.suggestion-item');
    items.forEach(item => {
        item.addEventListener('click', () => {
            input.value = item.textContent;
            resultBox.style.display = 'none';
        });
    });
}

document.addEventListener('DOMContentLoaded', () => {
    /*
    When the page is loaded, find a card and add event listeners for when the input box is clicked or typed into.
    */
    loadNewCard();
    
    const input = document.getElementById('guessInput');
    const resultBox = document.querySelector('.result-box');
    const resultList = resultBox.querySelector('ul');
    
    input.addEventListener('click', () => {
        resultBox.style.display = 'block';
        updateResults(input.value, resultList, input, resultBox);
    });

    input.addEventListener('input', () => {
        resultBox.style.display = 'block';
        updateResults(input.value, resultList, input, resultBox);
    });
    
    // Hide result box when clicking outside
    document.addEventListener('click', (e) => {
        if (!input.contains(e.target) && !resultBox.contains(e.target)) {
            resultBox.style.display = 'none';
        }
    });
});
