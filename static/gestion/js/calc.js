function updatePlateaux() {
    var t = document.getElementById('id_nombre_oeufs');
    var c = document.getElementById('id_oeufs_casses');
    var p = document.getElementById('preview-plateaux');
    if (!t || !c || !p) return;
    
    var total = parseInt(t.value) || 0;
    var casse = parseInt(c.value) || 0;
    var res = Math.floor(Math.max(0, total - casse) / 30);
    p.textContent = res + " 📦";
    p.style.color = "#0f5132";
    p.style.fontWeight = "bold";
}

document.addEventListener('DOMContentLoaded', function() {
    var t = document.getElementById('id_nombre_oeufs');
    var c = document.getElementById('id_oeufs_casses');
    if (t) t.addEventListener('input', updatePlateaux);
    if (c) c.addEventListener('input', updatePlateaux);
    
    // Force le calcul au chargement (passera de "--" à "0 📦" immédiatement)
    updatePlateaux();
});