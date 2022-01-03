using PowerSystems
using Plots

sys = System(0, enable_compression=true)
add_component!(sys, Bus(nothing))
for i in 1:3
    plant = RenewableDispatch(nothing)
    set_name!(plant, "plant$i")
    add_component!(sys, plant)
end

# required_metadata

metadata_file = "data/siip_timeseries_metadata.json"
add_time_series!(sys, metadata_file)
to_json(sys, "basic_system/sys.json", force=true)

ta = get_time_series_array(
    SingleTimeSeries,
    get_component(RenewableDispatch, sys, "plant1"),
    "max_active_power",
)
pyplot()
savefig(plot(ta), "basic_system/plant1_max_active_power.png")
