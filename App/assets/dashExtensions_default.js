window.dashExtensions = Object.assign({}, window.dashExtensions, {
    default: {
        function0: function onEachFeature(feature, layer) {
            layer.on('click', function(e) {
                alert(e.target.feature.properties.osm.name);
                // js2py.eval_js(update_sel_street(df_sel, e.target.feature.properties.osm.name))
                js2py.eval_js(print(e.target.feature.properties.osm.name))
            });
        },
        function1: function(feature, context) {
            // alert(typeof feature.properties.segment_id);
            return [9000001661, 9000001786, 9000002074, 9000003790, 9000004035, 9000004065, 9000004597, 9000004669, 9000004995, 9000005444, 9000005484, 9000006435].includes(feature.properties.segment_id);
        }
    }
});