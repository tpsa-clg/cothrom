import numpy as np
import random as rand
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import matplotlib.colors as cl


# orange="#FF7F00"
# black="k"
# purple="#9a4cdc"
# grey="#52555a"
# green="#53e97a"
# constituency_df.plot(column="seat", cmap=cl.LinearSegmentedColormap.from_list("cmap4", [green,black,orange,purple], N=4))
# plt.axis("off")
# plt.savefig("poster Wick.pdf", transparent=True, bbox_inches="tight")
# plt.show()












# Defining & calculating system quantities
seats = 5
JCs, JDs = (np.concatenate(([0.], 2. ** np.linspace(-3., 1., 5))) for _ in
            range(2))
JC_labels, JD_labels = ([r"0", r"2^{-3}", r"2^{-2}", r"2^{-1}", r"2^{0}",
                         r"2^{1}"] for _ in range(2))
p, r, Ts_len = .01, .9, 150
N, N_disc = 2000, 500
algs = ["Gibbs"]

TN, NI = Ts_len*N, N*districts
av_seat_pop, max_dist_pop = (sum(district_population) / seats,
                             max(district_population))
P_fac = 2 * (seats-1) * av_seat_pop
num_nei = [len(nei) for nei in district_neighbours]
borders, max_nei = sum(num_nei) // 2, max(num_nei)
ratios = r ** np.arange(0, Ts_len, 1)
Ts = np.array([[-ratios*((2*max_dist_pop/P_fac + JC*2/districts +
               JD*max_nei/borders)/np.log(1-p)) for JD in JDs] for JC in JCs])
seat_range = list(range(seats))


# Iterating over algorithms and coupling constants
(HP_evs, CPs, HC_evs, CCs, HD_evs, CDs, Cs, acc_avs, acc_vars) = (
    np.empty((len(JCs), len(JDs), len(algs), Ts_len)) for _ in range(9))
HP_opts, HC_opts, HD_opts = (np.empty((len(JCs), len(JDs), len(algs))) for _ in
                             range(3))
config_opts = np.empty((len(JCs), len(JDs), len(algs), districts))
colours = ["#004488", "#DDAA33", "#BB5566", "k"]
lines = [Line2D([0], [0], color=col, linestyle="solid") for col in colours]
labels = [r"$P$", r"$C$", r"$D$", r"$\alpha$"]
fig, ax = plt.subplots(2, 2, sharex=True, constrained_layout=True)
ax[0, 0].set_xlim(0, TN)
for c in range(2):
    ax[1, c].set_xlabel(r"$tn$")
ax[0, 0].set_ylabel(r"$H_P^{(tn)}$")
ax[1, 0].set_ylabel(r"$H_C^{(tn)}$")
ax[0, 1].set_ylabel(r"$H_D^{(tn)}$")
ax[1, 1].set_ylabel(r"$\alpha^{(tn)}$")
fig.legend(lines, labels, loc="center left", bbox_to_anchor=(1, .5))
for jc, (JC, JC_label) in enumerate(zip(JCs, JC_labels)):
    for jd, (JD, JD_label) in enumerate(zip(JDs, JD_labels)):
        T2 = Ts[jc, jd] ** 2
        for a, alg in enumerate(algs):
            # Initialising configuration
            district_seat = np.random.randint(seats, size=districts)

            seat_popdiff = np.full(seats, -av_seat_pop)
            for pop, seat in zip(district_population, district_seat):
                seat_popdiff[seat] += pop
            HP = sum(abs(seat_popdiff)) / P_fac

            seat_groups = [[] for _ in range(seats)]
            unvisited = set(range(districts))
            while unvisited:
                group = [unvisited.pop()]
                seat = district_seat[group[0]]
                i = 0
                while i < len(group):
                    for j in district_neighbours[group[i]]:
                        if j in unvisited and district_seat[j] == seat:
                            unvisited.remove(j)
                            group.append(j)
                    i += 1
                seat_groups[seat].append(set(group))
            HC = sum([abs(len(groups) - 1) for groups in seat_groups]
                     ) / districts

            HD = len([
                j for i, nei in enumerate(district_neighbours) for j in nei if
                district_seat[j] != district_seat[i]]) / (2 * borders)

            H = HP + JC*HC + JD*HD

            # Performing simulated annealing
            HPs, HCs, HDs, accs = [HP], [HC], [HD], []
            H_opt, HP_opt, HC_opt, HD_opt, config_opt = (H, HP, HC, HD,
                                                         district_seat.copy())

            if alg == "Metropolis":
                for t, T in enumerate(Ts[jc, jd]):
                    randints = np.random.randint(0, seats-1, NI)
                    ni = 0
                    for n in range(N):
                        acc = 0
                        for i, (pop, nei, curr) in enumerate(
                                zip(district_population, district_neighbours,
                                    district_seat)):
                            # Proposal seat
                            props = seat_range.copy()
                            props.pop(curr)
                            prop = props[randints[ni]]

                            # Change in population term
                            csd, psd = seat_popdiff[curr], seat_popdiff[prop]
                            ΔHP = (abs(csd - pop) - abs(csd) + abs(psd + pop) -
                                   abs(psd)) / P_fac

                            # Change in connectedness term
                            sgc, sgp = seat_groups[curr], seat_groups[prop]
                            for group in sgc:
                                if i in group:
                                    cig = group
                                    break
                            cngs, unvisited = [], cig.copy()
                            unvisited.remove(i)
                            while unvisited:
                                group = [unvisited.pop()]
                                j = 0
                                while j < len(group):
                                    for k in district_neighbours[group[j]]:
                                        if k in unvisited:
                                            unvisited.remove(k)
                                            group.append(k)
                                    j += 1
                                cngs.append(set(group))
                            pngs = []
                            nei_seats = district_seat[nei]
                            for (j, seat) in zip(nei, nei_seats):
                                if seat == prop:
                                    for group in sgp:
                                        if j in group:
                                            if group not in pngs:
                                                pngs.append(group)
                                            break
                            ΔHC = (abs(len(sgc) + len(cngs) - 2) - len(sgc) + 1
                                   + len(sgp) - len(pngs) - abs(len(sgp) - 1)
                                   ) / districts

                            # Change in compactness term
                            ΔHD = 0
                            for seat in nei_seats:
                                if seat == curr:
                                    ΔHD += 1
                                elif seat == prop:
                                    ΔHD -= 1
                            ΔHD /= borders

                            # Change in total Hamiltonian
                            ΔH = ΔHP + JC*ΔHC + JD*ΔHD

                            # Acceptance check
                            if (ΔH <= 0) or (rand.random() < np.e**(-ΔH/T)):
                                district_seat[i] = prop
                                H += ΔH
                                acc += 1

                                seat_popdiff[curr] -= pop
                                seat_popdiff[prop] += pop
                                HP += ΔHP

                                seat_groups[curr].remove(cig)
                                seat_groups[curr] += cngs
                                for group in pngs:
                                    seat_groups[prop].remove(group)
                                seat_groups[prop].append({i}.union(*pngs))
                                HC += ΔHC

                                HD += ΔHD

                                if H < H_opt:
                                    (H_opt, HP_opt, HC_opt, HD_opt, config_opt
                                     ) = H, HP, HC, HD, district_seat.copy()
                            ni += 1
                        HPs.append(HP)
                        HCs.append(HC)
                        HDs.append(HD)
                        accs.append(acc/districts)
                    print(jc, jd, a, t)
                del randints

            elif alg == "Gibbs":
                for t, T in enumerate(Ts[jc, jd]):
                    for n in range(N):
                        acc = 0
                        for i, (pop, nei, curr) in enumerate(
                                zip(district_population, district_neighbours,
                                    district_seat)):

                            # Changes in population term
                            csd = seat_popdiff[curr]
                            ΔHPs = (abs(csd - pop) - abs(csd) +
                                    abs(seat_popdiff + pop) - abs(seat_popdiff)
                                    ) / P_fac
                            ΔHPs[curr] = 0

                            # Changes in connectedness term
                            sgc = seat_groups[curr]
                            for group in sgc:
                                if i in group:
                                    cig = group
                                    break
                            cngs, unvisited = [], cig.copy()
                            unvisited.remove(i)
                            while unvisited:
                                group = [unvisited.pop()]
                                j = 0
                                while j < len(group):
                                    for k in district_neighbours[group[j]]:
                                        if k in unvisited:
                                            unvisited.remove(k)
                                            group.append(k)
                                    j += 1
                                cngs.append(set(group))
                            pngss = [[] for _ in range(seats)]
                            nei_seats = district_seat[nei]
                            for (j, seat) in zip(nei, nei_seats):
                                if seat != curr:
                                    for group in seat_groups[seat]:
                                        if j in group:
                                            if group not in pngss[seat]:
                                                pngss[seat].append(group)
                                            break

                            sgp_len = np.array([len(sgp) for sgp in
                                                seat_groups])
                            ΔHCs = (abs(len(sgc) + len(cngs) - 2) - len(sgc) +
                                    1 + sgp_len -
                                    np.array([len(pngs) for pngs in pngss]) -
                                    abs(sgp_len - 1)) / districts
                            ΔHCs[curr] = 0

                            # Changes in compactness term
                            ΔHDs = np.zeros(seats)
                            for seat in nei_seats:
                                ΔHDs[seat] -= 1
                            ΔHDs = (ΔHDs - ΔHDs[curr]) / borders

                            # Changes in total Hamiltonian and proposal
                            ΔHs = ΔHPs + JC*ΔHCs + JD*ΔHDs
                            prop_dist = np.exp(-ΔHs/T)
                            prop = np.random.choice(np.arange(0, seats, 1),
                                                    p=prop_dist/sum(prop_dist))
                            # CHANGE TO RAND.CHOICES!!! NO NEED FOR NORMALISING

                            if prop != curr:
                                district_seat[i] = prop
                                H += ΔHs[prop]
                                acc += 1

                                seat_popdiff[curr] -= pop
                                seat_popdiff[prop] += pop
                                HP += ΔHPs[prop]

                                seat_groups[curr].remove(cig)
                                seat_groups[curr] += cngs
                                for group in pngss[prop]:
                                    seat_groups[prop].remove(group)
                                seat_groups[prop].append(
                                    {i}.union(*pngss[prop]))
                                HC += ΔHCs[prop]

                                HD += ΔHDs[prop]

                                if H < H_opt:
                                    (H_opt, HP_opt, HC_opt, HD_opt, config_opt
                                     ) = H, HP, HC, HD, district_seat.copy()
                        HPs.append(HP)
                        HCs.append(HC)
                        HDs.append(HD)
                        accs.append(acc/districts)
                    print(jc, jd, a, t)

            (HP_opts[jc, jd, a], HC_opts[jc, jd, a], HD_opts[jc, jd, a],
             config_opts[jc, jd, a]) = (HP_opt, HC_opt, HD_opt,
                                        config_opt.copy())

            # Plotting evolutions and calculating expected values
            fig.suptitle(r"%s, $\frac{J_C}{J_P}=%s$, $\frac{J_D}{J_P}=%s$, %s"
                         % (counties, JC_label, JD_label, alg))

            ax[1, 1].plot(np.arange(1, TN+1, 1), accs, color=colours[3])
            accs = np.array([accs[t*N+N_disc:(t+1)*N] for t in range(Ts_len)])
            acc_avs[jc, jd, a], acc_vars[jc, jd, a] = (
                np.mean(accs, axis=1), np.var(accs, ddof=1, axis=1))
            del accs

            ax[0, 0].plot(HPs, color=colours[0])
            HPs = np.array([HPs[1+t*N+N_disc:1+(t+1)*N] for t in
                            range(Ts_len)])
            HP_evs[jc, jd, a], CPs[jc, jd, a] = (
                np.mean(HPs, axis=1), np.var(HPs, ddof=1, axis=1) / T2)
            Hs = HPs.copy()
            del HPs

            ax[1, 0].plot(HCs, color=colours[1])
            HCs = np.array([HCs[1+t*N+N_disc:1+(t+1)*N] for t in
                            range(Ts_len)])
            HC_evs[jc, jd, a], CCs[jc, jd, a] = (
                np.mean(HCs, axis=1), np.var(HCs, ddof=1, axis=1) / T2)
            Hs += JC * HCs
            del HCs

            ax[0, 1].plot(HDs, color=colours[2])
            HDs = np.array([HDs[1+t*N+N_disc:1+(t+1)*N] for t in
                            range(Ts_len)])
            HD_evs[jc, jd, a], CDs[jc, jd, a] = (
                np.mean(HDs, axis=1), np.var(HDs, ddof=1, axis=1) / T2)
            Hs += JD * HDs
            del HDs
            Cs[jc, jd, a] = np.var(Hs, ddof=1, axis=1) / T2
            del Hs

            for row in range(2):
                for col in range(2):
                    ax[row, col].relim()
                    ax[row, col].autoscale(axis="y")
            fig.savefig("%s/Samples vs nt (%s, JC = %s, JD = %s, %s).pdf" %
                        (counties, counties, JC, JD, alg), bbox_inches="tight")
            for row in range(2):
                for col in range(2):
                    for line in ax[row, col].get_lines():
                        line.remove()
            del line
plt.close(fig)
del fig, ax


# Plotting optimal configurations
for jc, JC in enumerate(JCs):
    for jd, JD in enumerate(JDs):
        for a, alg in enumerate(algs):
            district_data["seat"] = config_opts[jc, jd, a]
            district_data.explore(column="seat").save(
                "%s/Optimal configuration (JC = %s, JD = %s, %s).html" %
                (counties, JC, JD, alg))
district_EDID, district_geometry = (district_data.ED_ID.values,
                                    district_data.geometry.values)
del district_data


# Plotting expected values and specific heat capacities
fig, ax = plt.subplots(2, len(algs), sharex=True, sharey="row",
                       constrained_layout=True)
ax[0, 0].set_xscale("log")
ax[0, 0].set_ylim(-.05, 1.05)
ax[0, 0].set_ylabel(
    r"$\langle H_P\rangle$, $\langle H_C\rangle$, $\langle H_D\rangle$, $\bar{\alpha}$"
    )
ax[1, 0].set_ylabel(r"$C_P$, $C_C$, $C_D$")
ax_twin = [ax[1, a].twinx() for a in range(len(algs))]
ax_twin[0].set_yticklabels([])
ax_twin[-1].set_ylabel(r"$\mathrm{Var}\left(\bar{\alpha}\right)$")
for a, alg in enumerate(algs):
    ax[0, a].set_title(r"%s" % alg)
    ax[1, a].set_xlabel(r"$\frac{T}{J_P}$")
    ax[1, a].set_zorder(1)
    ax[1, a].set_frame_on(False)
fig.legend(lines, labels, loc="center left", bbox_to_anchor=(1, .5))
for jc, (JC, JC_label) in enumerate(zip(JCs, JC_labels)):
    for jd, (JD, JD_label) in enumerate(zip(JDs, JD_labels)):
        ax[0, 0].set_xlim(Ts[jc, jd, -1], Ts[jc, jd, 0])
        fig.suptitle(r"%s, $\frac{J_C}{J_P}=%s$, $\frac{J_D}{J_P}=%s$" %
                     (counties, JC_label, JD_label))
        for a in range(len(algs)):
            ax[0, a].plot(Ts[jc, jd], acc_avs[jc, jd, a], color=colours[3])
            ax[0, a].plot(Ts[jc, jd], HD_evs[jc, jd, a], color=colours[2])
            ax[0, a].plot(Ts[jc, jd], HC_evs[jc, jd, a], color=colours[1])
            ax[0, a].plot(Ts[jc, jd], HP_evs[jc, jd, a], color=colours[0])

            ax_twin[a].plot(
                [Ts[jc, jd, -1], Ts[jc, jd, 0]],
                [np.min(acc_vars[jc, jd]), np.max(acc_vars[jc, jd])], alpha=0.)
            ax_twin[a].plot(Ts[jc, jd], acc_vars[jc, jd, a], color=colours[3])
            ax[1, a].plot(Ts[jc, jd], CDs[jc, jd, a], color=colours[2])
            ax[1, a].plot(Ts[jc, jd], CCs[jc, jd, a], color=colours[1])
            ax[1, a].plot(Ts[jc, jd], CPs[jc, jd, a], color=colours[0])

            ax[1, a].relim()
            ax_twin[a].relim()
        ax[1, 0].autoscale(axis="y")
        ax_twin[0].autoscale(axis="y")
        fig.savefig("%s/Energies & heat capacities (%s, JC = %s, JD = %s).pdf"
                    % (counties, counties, JC, JD), bbox_inches="tight")
        for a in range(len(algs)):
            for A in [ax[0, a], ax[1, a], ax_twin[a]]:
                for line in A.get_lines():
                    line.remove()
        del line
plt.close(fig)
del fig, ax, ax_twin

JC_cm, JD_cm = (
    cl.LinearSegmentedColormap.from_list("JC_cm", ["#C2A5CF", "#762A83"],
                                         N=len(JCs)),
    cl.LinearSegmentedColormap.from_list("JD_cm", ["#ACD39E", "#1B7837"],
                                         N=len(JDs)))
JC_locs, JD_locs = (np.linspace(.5/len(JCs), 1. - .5/len(JCs), len(JCs)),
                    np.linspace(.5/len(JDs), 1. - .5/len(JDs), len(JDs)))
JC_ticks, JD_ticks = ([r"$" + JC_label + r"$" for JC_label in JC_labels],
                      [r"$" + JD_label + r"$" for JD_label in JD_labels])

############## below not changed for algorithms ##############

fig, ax = plt.subplots(2, len(JDs), sharex="col", constrained_layout=True)
fig.supxlabel(r"$\frac{T}{J_P}$")
fig.suptitle(r"%s" % counties)

cbar = fig.colorbar(plt.cm.ScalarMappable(cmap=JC_cm), ax=ax[:, :],
                    location="right", label=r"$\frac{J_C}{J_P}$")
cbar.set_ticks(JC_locs)
cbar.set_ticklabels(JC_ticks)

ax[0, 0].set_ylabel(r"$H_P$")
ax[1, 0].set_ylabel(r"$C_P$")
for jd, JD_label in enumerate(JD_labels):
    ax[0, jd].set_xscale("log")
    ax[0, jd].set_xlim(min(Ts[:, jd, -1]), max(Ts[:, jd, 0]))
    ax[0, jd].set_title(r"$\frac{J_D}{J_P}=%s$" % JD_label)
    for jc, JC_loc in enumerate(JC_locs):
        ax[0, jd].plot(Ts[jc, jd], HP_evs[jc, jd], color=JC_cm(JC_loc))
        ax[1, jd].plot(Ts[jc, jd], CPs[jc, jd], color=JC_cm(JC_loc))
fig.savefig(
    "%s/Population energy & heat capacity (%s, JC colorbar, JD columns).pdf" %
    (counties, counties))

ax[0, 0].set_ylabel(r"$H_C$")
ax[1, 0].set_ylabel(r"$C_C$")
for jd in range(len(JDs)):
    for i in range(2):
        for line in ax[i, jd].get_lines():
            line.remove()
    del line
    for jc, JC_loc in enumerate(JC_locs):
        ax[0, jd].plot(Ts[jc, jd], HC_evs[jc, jd], color=JC_cm(JC_loc))
        ax[1, jd].plot(Ts[jc, jd], CCs[jc, jd], color=JC_cm(JC_loc))
    for i in range(2):
        ax[i, jd].relim()
        ax[i, jd].autoscale(axis="y")
fig.savefig(
    "%s/Connectedness energy & heat capacity (%s, JC colorbar, JD columns).pdf"
    % (counties, counties))

ax[0, 0].set_ylabel(r"$H_D$")
ax[1, 0].set_ylabel(r"$C_D$")
for jd in range(len(JDs)):
    for i in range(2):
        for line in ax[i, jd].get_lines():
            line.remove()
    del line
    for jc, JC_loc in enumerate(JC_locs):
        ax[0, jd].plot(Ts[jc, jd], HD_evs[jc, jd], color=JC_cm(JC_loc))
        ax[1, jd].plot(Ts[jc, jd], CDs[jc, jd], color=JC_cm(JC_loc))
    for i in range(2):
        ax[i, jd].relim()
        ax[i, jd].autoscale(axis="y")
fig.savefig(
    "%s/Compactness energy & heat capacity (%s, JC colorbar, JD columns).pdf" %
    (counties, counties))

ax[0, 0].set_ylabel(r"$\bar{\alpha}$")
ax[1, 0].set_ylabel(r"$\mathrm{Var}\left(\bar{\alpha}\right)$")
for jd in range(len(JDs)):
    for i in range(2):
        for line in ax[i, jd].get_lines():
            line.remove()
    del line
    for jc, JC_loc in enumerate(JC_locs):
        ax[0, jd].plot(Ts[jc, jd], acc_avs[jc, jd], color=JC_cm(JC_loc))
        ax[1, jd].plot(Ts[jc, jd], acc_vars[jc, jd], color=JC_cm(JC_loc))
    for i in range(2):
        ax[i, jd].relim()
        ax[i, jd].autoscale(axis="y")
fig.savefig("%s/Acceptance rate & variance (%s, JC colorbar, JD columns).pdf" %
            (counties, counties))

cbar.remove()
cbar = fig.colorbar(plt.cm.ScalarMappable(cmap=JD_cm), ax=ax[:, :],
                    location="right", label=r"$\frac{J_D}{J_P}$")
cbar.set_ticks(JD_locs)
cbar.set_ticklabels(JD_ticks)

ax[0, 0].set_ylabel(r"$H_P$")
ax[1, 0].set_ylabel(r"$C_P$")
for jc, JC_label in enumerate(JC_labels):
    for i in range(2):
        for line in ax[i, jc].get_lines():
            line.remove()
    del line
    ax[0, jc].set_xlim(min(Ts[jc, :, -1]), max(Ts[jc, :, 0]))
    ax[0, jc].set_title(r"$\frac{J_C}{J_P}=%s$" % JC_label)
    for jd, JD_loc in enumerate(JD_locs):
        ax[0, jc].plot(Ts[jc, jd], HP_evs[jc, jd], color=JD_cm(JD_loc))
        ax[1, jc].plot(Ts[jc, jd], CPs[jc, jd], color=JD_cm(JD_loc))
    for i in range(2):
        ax[i, jc].relim()
        ax[i, jc].autoscale(axis="y")
fig.savefig(
    "%s/Population energy & heat capacity (%s, JD colorbar, JC columns).pdf" %
    (counties, counties))

ax[0, 0].set_ylabel(r"$H_C$")
ax[1, 0].set_ylabel(r"$C_C$")
for jc in range(len(JCs)):
    for i in range(2):
        for line in ax[i, jc].get_lines():
            line.remove()
    del line
    for jd, JD_loc in enumerate(JD_locs):
        ax[0, jc].plot(Ts[jc, jd], HC_evs[jc, jd], color=JD_cm(JD_loc))
        ax[1, jc].plot(Ts[jc, jd], CCs[jc, jd], color=JD_cm(JD_loc))
    for i in range(2):
        ax[i, jc].relim()
        ax[i, jc].autoscale(axis="y")
fig.savefig(
    "%s/Connectedness energy & heat capacity (%s, JD colorbar, JC columns).pdf"
    % (counties, counties))

ax[0, 0].set_ylabel(r"$H_D$")
ax[1, 0].set_ylabel(r"$C_D$")
for jc in range(len(JCs)):
    for i in range(2):
        for line in ax[i, jc].get_lines():
            line.remove()
    del line
    for jd, JD_loc in enumerate(JD_locs):
        ax[0, jc].plot(Ts[jc, jd], HD_evs[jc, jd], color=JD_cm(JD_loc))
        ax[1, jc].plot(Ts[jc, jd], CDs[jc, jd], color=JD_cm(JD_loc))
    for i in range(2):
        ax[i, jc].relim()
        ax[i, jc].autoscale(axis="y")
fig.savefig(
    "%s/Compactness energy & heat capacity (%s, JD colorbar, JC columns).pdf" %
    (counties, counties))

ax[0, 0].set_ylabel(r"$\bar{\alpha}$")
ax[1, 0].set_ylabel(r"$\mathrm{Var}\left(\bar{\alpha}\right)$")
for jc in range(len(JCs)):
    for i in range(2):
        for line in ax[i, jc].get_lines():
            line.remove()
    del line
    for jd, JD_loc in enumerate(JD_locs):
        ax[0, jc].plot(Ts[jc, jd], acc_avs[jc, jd], color=JD_cm(JD_loc))
        ax[1, jc].plot(Ts[jc, jd], acc_vars[jc, jd], color=JD_cm(JD_loc))
    for i in range(2):
        ax[i, jc].relim()
        ax[i, jc].autoscale(axis="y")
fig.savefig("%s/Acceptance rate & variance (%s, JD colorbar, JC columns).pdf" %
            (counties, counties))

plt.close(fig)
del fig, ax, cbar


# Plotting critical temperatures and optimal Hamiltonians
# 4 x 2 subplot: row = T_c/H_P*/H_C*/H_D* vs, col = vs JD/JC & colorbar = JC/JD


# av_seat_pop, max_dist_pop = (sum(district_population) / seats,
#                              max(district_population))
# ε = abs(av_seat_pop - int(av_seat_pop + .5))
# if ε == 0:
#     ΔHPs = np.arange(-2*max_dist_pop, 2*max_dist_pop+2, 2)
# elif ε == .5:
#     ΔHPs = np.arange(-2*max_dist_pop, 2*max_dist_pop+1, 1)
# else:
#     temp = np.array([2*(i+ε) for i in range(max_dist_pop)])
#     temp = np.concatenate((temp, temp-2*max_dist_pop))
#     ΔHPs = np.concatenate((np.arange(-2*max_dist_pop, 2*max_dist_pop+2, 2),
#                             temp, -temp))
#     del temp
# ΔHPs /= 2 * (seats-1) * av_seat_pop

# ΔHCs = np.arange(-2, 2+1, 1) / districts

# num_nei = [len(i) for i in district_neighbours]
# borders, max_nei = sum(num_nei) // 2, max(num_nei)
# ΔHDs = np.arange(-max_nei, max_nei+1, 1) / borders

# ΔHs = np.array([ΔH for p in ΔHPs for d in ΔHDs for c in ΔHCs if
#                 (ΔH := p + JD*d + JC*c) > 0])
# ΔH_min, ΔH_max = min(ΔHs), max(ΔHs)
# del ΔHs, ΔHPs, ΔHCs, ΔHDs

# p, r = .01, .9
# T_min, T_max = -ΔH_min/np.log(p), -ΔH_max/np.log(1-p)
# Ts = [T_max]
# while Ts[-1] > T_min:
#     Ts.append(r * Ts[-1])
# Ts = np.array(Ts)
