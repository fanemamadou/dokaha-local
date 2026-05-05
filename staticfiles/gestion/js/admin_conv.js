(function(){
    function updateConv(){
        var input = document.getElementById('id_nombre_oeufs');
        if(!input) return;
        var preview = document.getElementById('admin-conv-preview');
        if(!preview){
            preview = document.createElement('div');
            preview.id = 'admin-conv-preview';
            preview.style.cssText = 'margin-top:5px; font-weight:bold; color:#2e7d32;';
            var row = input.closest('.form-row'); // Structure standard Django Admin
            if(row) row.appendChild(preview);
        }
        var v = parseInt(input.value) || 0;
        preview.textContent = v > 0 ? ('📊 '+Math.floor(v/30)+' 📦'+(v%30>0?' +'+v%30+' 🥚':'')+' = '+v+' œufs') : '';
    }
    document.addEventListener('DOMContentLoaded', function(){ setTimeout(updateConv, 500); });
    document.addEventListener('input', function(e){ if(e.target.id==='id_nombre_oeufs') updateConv(); });
})();
