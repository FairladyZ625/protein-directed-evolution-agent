# Scheduling note (no scientific change)

To reduce gateway latency, after the six reference trials and FULL/SEMI seed42 were started,
the four still-unstarted FULL/SEMI seed0/7 trials were assigned independent single-process runners.
Each process uses one BLAS/OpenMP thread. They run the identical frozen run_autoresearch code
and registered parameters, once each. Explicit incomplete metrics claims prevent the older serial
schedulers from repeating those trials; those schedulers will stop at their existing-output guard
after seed42. Guard exceptions are scheduling stops, not API/model failures or discarded trials.
Real metrics replace incomplete claims only after 6x48 budget and event-chain verification.
