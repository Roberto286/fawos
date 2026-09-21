#!/bin/bash
dnf5 -y copr enable bieszczaders/kernel-cachyos

dnf5 -y remove kernel kernel-core kernel-modules kernel-modules-core kernel-modules-extra kernel-devel kernel-devel-matched --set-opt=protected_packages= --allowerasing

dnf5 -y install kernel-cachyos kernel-cachyos-devel-matched

dnf5 -y copr disable bieszczaders/kernel-cachyos
