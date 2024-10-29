document.addEventListener('DOMContentLoaded', function() {
    const vejaMaisBtn = document.getElementById('vejaMais');
    const imagensOcultas = document.querySelectorAll('.imagem-container.oculta');
    const copyButtons = document.querySelectorAll('.copy-btn');
    const downloadButtons = document.querySelectorAll('.download-btn');
    const filtroSelect = document.getElementById('categoria-filtro');
    const imagensContainers = document.querySelectorAll('.imagem-container');

    vejaMaisBtn.addEventListener('click', function() {
        imagensOcultas.forEach((container, index) => {
            setTimeout(() => {
                container.classList.remove('oculta');
                container.style.animation = 'fadeIn 0.5s ease forwards';
            }, index * 100);
        });
        this.style.display = 'none';
    });

    copyButtons.forEach(button => {
        button.addEventListener('click', function() {
            const prompt = this.previousElementSibling.textContent;
            navigator.clipboard.writeText(prompt).then(() => {
                const originalIcon = this.innerHTML;
                this.innerHTML = '<i class="fas fa-check"></i>';
                this.style.color = '#4CAF50';
                
                setTimeout(() => {
                    this.innerHTML = originalIcon;
                    this.style.color = '';
                }, 2000);
            }).catch(err => {
                console.error('Erro ao copiar texto: ', err);
            });
        });
    });

    downloadButtons.forEach(button => {
        button.addEventListener('click', function() {
            const img = this.previousElementSibling;
            const imgUrl = img.src;
            const fileName = img.alt + '.png';

            fetch(imgUrl)
                .then(response => response.blob())
                .then(blob => {
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.style.display = 'none';
                    a.href = url;
                    a.download = fileName;
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                })
                .catch(err => console.error('Erro ao baixar imagem:', err));
        });
    });

    // Funcionalidade de filtragem
    filtroSelect.addEventListener('change', function() {
        const categoriaSelecionada = this.value;
        imagensContainers.forEach(container => {
            if (categoriaSelecionada === 'todas' || container.dataset.categoria === categoriaSelecionada) {
                container.style.display = 'block';
            } else {
                container.style.display = 'none';
            }
        });

        // Reajusta a visibilidade do botão "Ver mais"
        if (categoriaSelecionada === 'todas') {
            vejaMaisBtn.style.display = 'block';
            imagensOcultas.forEach(container => {
                container.classList.add('oculta');
            });
        } else {
            vejaMaisBtn.style.display = 'none';
            imagensOcultas.forEach(container => {
                container.classList.remove('oculta');
            });
        }
    });

    // Adiciona funcionalidade para menu responsivo
    const menuItems = document.querySelectorAll('.sidebar ul li a');
    menuItems.forEach(item => {
        item.addEventListener('click', function(e) {
            if (window.innerWidth <= 768) {
                e.preventDefault();
                const targetId = this.getAttribute('href').substring(1);
                const targetElement = document.getElementById(targetId);
                if (targetElement) {
                    targetElement.scrollIntoView({ behavior: 'smooth' });
                }
            }
        });
    });
});