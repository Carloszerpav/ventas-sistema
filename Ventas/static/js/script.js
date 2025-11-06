// ========================================
// SISTEMA DE VENTAS - JavaScript por Carloszerpav
// ========================================
// Este es el JavaScript de mi sistema de ventas
// Maneja todas las interacciones del usuario

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar el sistema de temas
    initThemeSystem();
    
    // Inicializar funcionalidades del formulario
    initFormFeatures();
    
    // Inicializar animaciones
    initAnimations();
    
    // Inicializar validaciones
    initValidations();
    
    // Inicializar búsqueda
    initSearch();
    
    // Inicializar header colapsable
    initCollapsibleHeader();
});

// ========================================
// SISTEMA DE TEMAS - Carloszerpav
// ========================================
// Aquí manejo el cambio entre modo oscuro y claro
// Me gusta tener ambas opciones para trabajar

function initThemeSystem() {
    const themeToggle = document.getElementById('theme-toggle');
    const html = document.documentElement;
    
    // Obtener tema guardado o usar preferencia del sistema
    const savedTheme = localStorage.getItem('theme');
    const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    // Aplicar tema inicial
    if (savedTheme) {
        html.setAttribute('data-theme', savedTheme);
    } else if (systemPrefersDark) {
        html.setAttribute('data-theme', 'dark');
    } else {
        html.setAttribute('data-theme', 'light');
    }
    
    // Event listener para el toggle
    if (themeToggle) {
    themeToggle.addEventListener('click', function() {
            const currentTheme = html.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        // Cambiar tema
            html.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
            
            // Animación del botón
            themeToggle.style.transform = 'scale(0.9)';
            setTimeout(() => {
                themeToggle.style.transform = 'scale(1)';
            }, 150);
        
        // Mostrar notificación
            showNotification(`Modo ${newTheme === 'dark' ? 'oscuro' : 'claro'} activado`, 'success');
        });
    }
    
    // Escuchar cambios en preferencias del sistema
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
        if (!localStorage.getItem('theme')) {
            html.setAttribute('data-theme', e.matches ? 'dark' : 'light');
        }
    });
}

// ========================================
// FUNCIONALIDADES DEL FORMULARIO - Carloszerpav
// ========================================
// Aquí manejo todo lo del formulario de ventas
// Validaciones, cálculos automáticos, etc.

function initFormFeatures() {
    const form = document.querySelector('.venta-form');
    const valorTotalInput = document.getElementById('valor_total');
    const abonoInput = document.getElementById('abono');
    const clienteInput = document.getElementById('cliente');
    
    if (form) {
        // Auto-calcular saldo pendiente
        if (valorTotalInput && abonoInput) {
            [valorTotalInput, abonoInput].forEach(input => {
                input.addEventListener('input', calculatePendingAmount);
            });
        }
        
        // Auto-completar fecha actual
    const fechaInput = document.getElementById('fecha');
        if (fechaInput && !fechaInput.value) {
            fechaInput.value = new Date().toISOString().split('T')[0];
        }
    
    // Validación en tiempo real
        if (clienteInput) {
    clienteInput.addEventListener('input', function() {
                validateField(this, this.value.trim().length > 0, 'El nombre del cliente es requerido');
            });
        }
        
        // Submit del formulario
    form.addEventListener('submit', function(e) {
        if (!validateForm()) {
            e.preventDefault();
            showNotification('Por favor, corrige los errores en el formulario', 'error');
        }
    });
}
}

function calculatePendingAmount() {
    const valorTotal = parseFloat(document.getElementById('valor_total').value) || 0;
    const abono = parseFloat(document.getElementById('abono').value) || 0;
    
    // Mostrar saldo pendiente en tiempo real (opcional)
    const pendingAmount = valorTotal - abono;
    
    // Actualizar visualmente si hay un elemento para mostrar el pendiente
    const pendingElement = document.querySelector('.pending-preview');
    if (pendingElement) {
        pendingElement.textContent = formatCurrency(pendingAmount);
        pendingElement.className = pendingAmount > 0 ? 'pending-preview pending' : 'pending-preview';
    }
}

function validateField(field, isValid, message) {
    const errorElement = field.parentNode.querySelector('.field-error');
    
    if (!isValid) {
        field.classList.add('error');
        if (!errorElement) {
            const error = document.createElement('div');
            error.className = 'field-error';
            error.textContent = message;
            error.style.color = 'var(--danger-color)';
            error.style.fontSize = '0.75rem';
            error.style.marginTop = '0.25rem';
            field.parentNode.appendChild(error);
        }
    } else {
        field.classList.remove('error');
        if (errorElement) {
            errorElement.remove();
        }
    }
}

function validateForm() {
    const cliente = document.getElementById('cliente').value.trim();
    const valorTotal = parseFloat(document.getElementById('valor_total').value);
    const abono = parseFloat(document.getElementById('abono').value) || 0;
    
    let isValid = true;
    
    // Validar cliente
    if (!cliente) {
        validateField(document.getElementById('cliente'), false, 'El nombre del cliente es requerido');
        isValid = false;
    }
    
    // Validar valor total
    if (!valorTotal || valorTotal <= 0) {
        validateField(document.getElementById('valor_total'), false, 'El valor total debe ser mayor a 0');
        isValid = false;
    }
    
    // Validar abono
    if (abono < 0) {
        validateField(document.getElementById('abono'), false, 'El abono no puede ser negativo');
        isValid = false;
    }
    
    // Validar que el abono no sea mayor al valor total
    if (abono > valorTotal) {
        validateField(document.getElementById('abono'), false, 'El abono no puede ser mayor al valor total');
        isValid = false;
    }
    
    return isValid;
}

// ========================================
// ANIMACIONES Y EFECTOS
// ========================================

function initAnimations() {
    // Animación de entrada para las tarjetas
    const cards = document.querySelectorAll('.stat-card, .form-container, .ventas-container, .rubros-container');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, {
        threshold: 0.1
    });
    
    cards.forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(card);
    });
    
    // Animación para las filas de la tabla
    const tableRows = document.querySelectorAll('.venta-row');
    tableRows.forEach((row, index) => {
        row.style.opacity = '0';
        row.style.transform = 'translateX(-20px)';
        row.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
        
        setTimeout(() => {
            row.style.opacity = '1';
            row.style.transform = 'translateX(0)';
        }, index * 100);
    });
}

// ========================================
// VALIDACIONES ADICIONALES
// ========================================

function initValidations() {
    // Validar números en campos numéricos
    const numericInputs = document.querySelectorAll('input[type="number"]');
    numericInputs.forEach(input => {
        input.addEventListener('input', function() {
            const value = parseFloat(this.value);
            if (this.value && value < 0) {
                this.value = 0;
                showNotification('No se permiten valores negativos', 'warning');
            }
        });
    });
    
    // Validar fecha
    const fechaInput = document.getElementById('fecha');
    if (fechaInput) {
        fechaInput.addEventListener('change', function() {
            const selectedDate = new Date(this.value);
            const today = new Date();
            
            if (selectedDate > today) {
                showNotification('La fecha no puede ser futura', 'warning');
                this.value = today.toISOString().split('T')[0];
            }
        });
    }
}

// ========================================
// NOTIFICACIONES
// ========================================

function showNotification(message, type = 'info') {
    // Crear elemento de notificación
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas ${getNotificationIcon(type)}"></i>
            <span>${message}</span>
        </div>
        <button class="notification-close">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    // Estilos de la notificación
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 1rem;
        box-shadow: var(--shadow-lg);
        z-index: 1000;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        min-width: 300px;
        transform: translateX(100%);
        transition: transform 0.3s ease;
    `;
    
    // Agregar al DOM
    document.body.appendChild(notification);
    
    // Animar entrada
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 100);
    
    // Event listener para cerrar
    const closeBtn = notification.querySelector('.notification-close');
    closeBtn.addEventListener('click', () => {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            notification.remove();
        }, 300);
    });
    
    // Auto-cerrar después de 5 segundos
    setTimeout(() => {
        if (notification.parentNode) {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                    notification.remove();
            }, 300);
        }
    }, 5000);
}

function getNotificationIcon(type) {
    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };
    return icons[type] || icons.info;
}

// ========================================
// UTILIDADES
// ========================================

function formatCurrency(amount) {
    return new Intl.NumberFormat('es-CO', {
        style: 'currency',
        currency: 'COP',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(amount);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('es-CO', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    });
}

// ========================================
// FUNCIONES DE EXPORTACIÓN (OPCIONAL)
// ========================================

function exportToCSV() {
    // Implementar exportación a CSV
    showNotification('Función de exportación en desarrollo', 'info');
}

function exportToPDF() {
    // Implementar exportación a PDF
    showNotification('Función de exportación en desarrollo', 'info');
}

// ========================================
// EVENTOS GLOBALES
// ========================================

// Confirmar eliminación
document.addEventListener('click', function(e) {
    if (e.target.closest('.btn-delete')) {
        const confirmed = confirm('¿Estás seguro de que quieres eliminar esta venta?');
        if (!confirmed) {
        e.preventDefault();
        }
    }
});

// Mejorar accesibilidad
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + K para cambiar tema
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        document.getElementById('theme-toggle').click();
    }
    
    // Escape para cerrar notificaciones
    if (e.key === 'Escape') {
        const notifications = document.querySelectorAll('.notification');
        notifications.forEach(notification => {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                notification.remove();
            }, 300);
        });
    }
});

// ========================================
// INICIALIZACIÓN FINAL
// ========================================

// Mostrar mensaje de bienvenida
setTimeout(() => {
    if (document.querySelector('.empty-state')) {
        showNotification('¡Bienvenido! Comienza agregando tu primera venta', 'info');
    }
}, 1000);

// ========================================
// FUNCIONALIDAD DE BÚSQUEDA
// ========================================

function initSearch() {
    const searchInput = document.getElementById('search-input');
    const searchForm = document.querySelector('.search-form');
    
    if (!searchInput || !searchForm) return;
    
    let searchTimeout;
    
    // Búsqueda en tiempo real con debounce
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        
        searchTimeout = setTimeout(() => {
            const query = this.value.trim();
            
            if (query.length >= 2 || query.length === 0) {
                // Realizar búsqueda automática
                performSearch(query);
            }
        }, 300); // Esperar 300ms después de que el usuario deje de escribir
    });
    
    // Búsqueda al presionar Enter
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            searchForm.submit();
        }
    });
    
    // Limpiar búsqueda con Ctrl+L
    searchInput.addEventListener('keydown', function(e) {
        if (e.ctrlKey && e.key === 'l') {
            e.preventDefault();
            this.value = '';
            performSearch('');
        }
    });
}

function performSearch(query) {
    const currentUrl = new URL(window.location);
    
    if (query) {
        currentUrl.searchParams.set('q', query);
    } else {
        currentUrl.searchParams.delete('q');
    }
    
    // Actualizar URL sin recargar la página
    window.history.pushState({}, '', currentUrl);
    
    // Realizar la búsqueda
    fetch(currentUrl.pathname + currentUrl.search)
        .then(response => response.text())
        .then(html => {
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            
            // Actualizar solo la tabla de ventas
            const newTable = doc.querySelector('.table-container');
            const currentTable = document.querySelector('.table-container');
            
            if (newTable && currentTable) {
                currentTable.innerHTML = newTable.innerHTML;
            }
            
            // Actualizar contador de resultados
            const newResults = doc.querySelector('.search-results');
            const currentResults = document.querySelector('.search-results');
            
            if (newResults && currentResults) {
                currentResults.innerHTML = newResults.innerHTML;
            } else if (newResults && !currentResults) {
                const searchContainer = document.querySelector('.search-container');
                if (searchContainer) {
                    searchContainer.appendChild(newResults);
                }
            } else if (!newResults && currentResults) {
                currentResults.remove();
            }
            
            // Actualizar el input de búsqueda
            const newInput = doc.getElementById('search-input');
            if (newInput) {
                document.getElementById('search-input').value = newInput.value;
            }
        })
        .catch(error => {
            console.error('Error en la búsqueda:', error);
            // Fallback: recargar la página
            window.location.href = currentUrl.pathname + currentUrl.search;
        });
}

// ========================================
// VALIDACIÓN DE RUBROS - Carloszerpav
// ========================================
// Aquí me aseguro de que siempre seleccionen al menos un rubro
// Es importante para mis estadísticas

function initRubrosValidation() {
    const form = document.querySelector('.venta-form');
    const rubrosCheckboxes = document.querySelectorAll('input[name="rubros"]');
    const rubrosGrid = document.querySelector('.rubros-grid');
    
    if (!form || !rubrosCheckboxes.length) return;
    
    // Función para validar rubros
    function validateRubros() {
        const checkedRubros = document.querySelectorAll('input[name="rubros"]:checked');
        const isValid = checkedRubros.length > 0;
        
        // Actualizar estilo visual
        if (rubrosGrid) {
            if (isValid) {
                rubrosGrid.style.border = '';
                rubrosGrid.style.backgroundColor = '';
                rubrosGrid.style.padding = '';
            } else {
                rubrosGrid.style.border = '1px solid var(--danger-color)';
                rubrosGrid.style.backgroundColor = 'rgba(239, 68, 68, 0.05)';
                rubrosGrid.style.padding = '0.5rem';
                rubrosGrid.style.borderRadius = '8px';
            }
        }
        
        return isValid;
    }
    
    // Event listeners para los checkboxes
    rubrosCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', validateRubros);
    });
    
    // Validación al enviar el formulario
    form.addEventListener('submit', function(e) {
        if (!validateRubros()) {
            e.preventDefault();
            showNotification('Debe seleccionar al menos un rubro', 'error');
            
            // Hacer scroll al área de rubros
            if (rubrosGrid) {
                rubrosGrid.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }
    });
    
    // Validación inicial
    validateRubros();
}

// Agregar la inicialización de validación de rubros
document.addEventListener('DOMContentLoaded', function() {
    initRubrosValidation();
});

// ========================================
// HEADER COLAPSABLE MEJORADO - Carloszerpav
// ========================================
// Esta función hace que el header se reduzca al hacer scroll
// Optimizada para móviles con scroll suave y sin saltos

function initCollapsibleHeader() {
    const header = document.querySelector('.header');
    if (!header) return;
    
    let lastScrollTop = 0;
    let scrollThreshold = 100; // Píxeles a scrollear antes de colapsar
    let isScrolling = false;
    let scrollTimeout;
    
    // Solo activar en móviles o pantallas pequeñas
    if (window.innerWidth <= 768) {
        scrollThreshold = 30; // Menos scroll en móviles para respuesta más rápida
    }
    
    // Función para manejar el scroll con throttling
    function handleScroll() {
        if (isScrolling) return;
        
        isScrolling = true;
        requestAnimationFrame(() => {
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            
            // Detectar dirección del scroll
            if (scrollTop > lastScrollTop && scrollTop > scrollThreshold) {
                // Scrolling hacia abajo - colapsar header
                if (!header.classList.contains('header-collapsed')) {
                    header.classList.add('header-collapsed');
                }
            } else if (scrollTop < lastScrollTop || scrollTop <= scrollThreshold) {
                // Scrolling hacia arriba o cerca del top - expandir header
                if (header.classList.contains('header-collapsed')) {
                    header.classList.remove('header-collapsed');
                }
            }
            
            lastScrollTop = scrollTop;
            isScrolling = false;
        });
    }
    
    // Event listener optimizado para scroll
    window.addEventListener('scroll', handleScroll, { passive: true });
    
    // Manejo de touch para móviles
    let touchStartY = 0;
    let touchStartTime = 0;
    
    document.addEventListener('touchstart', function(e) {
        touchStartY = e.touches[0].clientY;
        touchStartTime = Date.now();
    }, { passive: true });
    
    document.addEventListener('touchend', function(e) {
        const touchEndY = e.changedTouches[0].clientY;
        const touchEndTime = Date.now();
        const scrollY = touchEndY - touchStartY;
        const touchDuration = touchEndTime - touchStartTime;
        
        // Solo procesar si es un scroll rápido (no un tap)
        if (Math.abs(scrollY) > 10 && touchDuration < 300) {
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            
            if (scrollY < 0 && scrollTop > scrollThreshold) {
                // Scroll hacia abajo
                header.classList.add('header-collapsed');
            } else if (scrollY > 0 || scrollTop <= scrollThreshold) {
                // Scroll hacia arriba
                header.classList.remove('header-collapsed');
            }
        }
    }, { passive: true });
    
    // Limpiar timeout al cambiar de página
    window.addEventListener('beforeunload', function() {
        if (scrollTimeout) {
            clearTimeout(scrollTimeout);
        }
    });
}

// Inicializar header colapsable
document.addEventListener('DOMContentLoaded', function() {
    initCollapsibleHeader();
});

// ========================================
// OPTIMIZACIONES PARA TECLADO MÓVIL - Carloszerpav
// ========================================
// Estas funciones evitan que la pantalla se mueva cuando aparece el teclado

function initMobileKeyboardOptimizations() {
    // Detectar si es un dispositivo móvil
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    
    if (!isMobile) return;
    
    // Variables para controlar el scroll
    let initialScrollTop = 0;
    let isKeyboardVisible = false;
    
    // Detectar cuando aparece el teclado
    function handleInputFocus(event) {
        const input = event.target;
        initialScrollTop = window.pageYOffset;
        
        // Hacer scroll suave al input para que sea visible
        setTimeout(() => {
            input.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'center',
                inline: 'nearest'
            });
        }, 300);
        
        isKeyboardVisible = true;
    }
    
    // Detectar cuando se oculta el teclado
    function handleInputBlur(event) {
        isKeyboardVisible = false;
        
        // Restaurar la posición del scroll si es necesario
        setTimeout(() => {
            if (!isKeyboardVisible) {
                window.scrollTo({
                    top: initialScrollTop,
                    behavior: 'smooth'
                });
            }
        }, 100);
    }
    
    // Aplicar a todos los inputs
    const inputs = document.querySelectorAll('input, select, textarea');
    inputs.forEach(input => {
        input.addEventListener('focus', handleInputFocus);
        input.addEventListener('blur', handleInputBlur);
    });
    
    // Prevenir scroll del body cuando el teclado está visible
    function preventBodyScroll(event) {
        if (isKeyboardVisible) {
            event.preventDefault();
        }
    }
    
    // Detectar cambios en el viewport (teclado aparece/desaparece)
    let viewportHeight = window.innerHeight;
    
    window.addEventListener('resize', function() {
        const newViewportHeight = window.innerHeight;
        
        if (newViewportHeight < viewportHeight) {
            // Teclado apareció
            isKeyboardVisible = true;
        } else if (newViewportHeight > viewportHeight) {
            // Teclado desapareció
            isKeyboardVisible = false;
        }
        
        viewportHeight = newViewportHeight;
    });
    
    // Optimizaciones específicas para iOS
    if (/iPad|iPhone|iPod/.test(navigator.userAgent)) {
        // Prevenir el comportamiento de zoom en inputs
        const metaViewport = document.querySelector('meta[name="viewport"]');
        if (metaViewport) {
            metaViewport.setAttribute('content', 
                'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no');
        }
        
        // Mejorar el comportamiento del scroll en iOS
        document.body.style.webkitOverflowScrolling = 'touch';
    }
}

// Inicializar optimizaciones para teclado móvil
document.addEventListener('DOMContentLoaded', function() {
    initMobileKeyboardOptimizations();
});
