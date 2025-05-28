document.addEventListener('keydown', function(event) {
    if (event.key === 'Enter') {
      searchCards();
    }
  });

async function searchCards() {
            const cardName = document.getElementById('cardName').value;
            const oracleText = document.getElementById('oracleText').value;
            const cmc = document.getElementById('cmc').value;
            const colors = Array.from(document.querySelectorAll('input[name="color"]:checked'))
                           .map(cb => cb.value);
            const color_filter = document.getElementById('colorLogic').value;
            
            let url = '/api/cards?';
            if (cardName) url += `name=${encodeURIComponent(cardName)}&`;
            if (oracleText) url += `oracle=${encodeURIComponent(oracleText)}&`;
            if (cmc) url += `cmc=${encodeURIComponent(cmc)}&`;
            if (colors.length > 0) {
                url += `colors=${encodeURIComponent(colors.join(','))}&`;
                url += `colorLogic=${encodeURIComponent(color_filter)}&`;
            }
            const response = await fetch(url);
            const cards = await response.json();
            
            console.log('API Response:', cards);
            displayResults(cards);
        }
        function displayResults(cards) {
            const resultsDiv = document.getElementById('results');
            resultsDiv.innerHTML = '';
            
            cards.forEach(card => {
                const cardDiv = document.createElement('div');
                cardDiv.className = 'card-item';
                cardDiv.style.border = 'none';

                if (card.face_image_uri_normal && card.card_faces && card.card_faces[1] && card.card_faces[1].image_uris) {
                    // card has multiple faces
                    const frontImage = card.face_image_uri_normal;
                    const backImage = card.card_faces[1].image_uris.normal;
                    
                    cardDiv.innerHTML = `
                        <div class="flip-card">
                            <img src="${frontImage}" alt="${card.name}" style="width: 100%;" data-front="${frontImage}" data-back="${backImage}">
                            <button onclick="flipCard(this)" class="flip-button">Flip</button>
                        </div>
                    `;
                } else {
                    // single faced card
                    const imageUrl = card.image_uri_normal;
                    if (imageUrl) {
                        cardDiv.innerHTML = `
                            <img src="${imageUrl}" alt="${card.name}" style="width: 100%;">
                        `;
                    }
                }
                
                resultsDiv.appendChild(cardDiv);
            });
        }

        function flipCard(button) {
            const img = button.previousElementSibling;
            const currentSrc = img.src;
            const frontSrc = img.dataset.front;
            const backSrc = img.dataset.back;
            
            img.src = currentSrc === frontSrc ? backSrc : frontSrc;
        }