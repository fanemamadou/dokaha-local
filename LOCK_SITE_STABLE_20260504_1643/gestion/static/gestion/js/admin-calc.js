django.jQuery(function($) {
    $('#id_nombre_oeufs').on('input change', function() {
        var v = parseInt($(this).val()) || 0;
        var html = v > 0 ? (Math.floor(v/30) + ' 📦' + (v%30>0 ? ' +' + v%30 + ' 🥚' : '') + ' = ' + v + ' œufs') : '--';
        if ($('#admin-conv-preview').length === 0) {
            $(this).closest('.form-row').append('<div id="admin-conv-preview" style="margin-top:6px; color:#2e7d32; font-weight:500;"></div>');
        }
        $('#admin-conv-preview').html(html);
    });
});
