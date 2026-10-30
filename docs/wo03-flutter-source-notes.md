# WO-03 preliminary fin flutter source note

## Primary source verified

Dennis J. Martin, *Summary of Flutter Experiences as a Guide to the Preliminary Design of Lifting Surfaces on Missiles*, NACA Technical Note 4197 (February 1958), [NTRS record](https://ntrs.nasa.gov/citations/19930085030) and [original PDF](https://ntrs.nasa.gov/api/citations/19930085030/downloads/19930085030.pdf). The NTRS PDF text exposes the appendix derivation and the figure captions. PDF screenshot retrieval for the empirical Figure 3/4 pages timed out in this review, so no numeric safe/unsafe chart boundary is transcribed here.

This is a primary US government technical note, specifically framed as a *preliminary* missile lifting-surface guide. It presents a chart-based empirical bending-torsion screen based on accumulated wing, missile, wind-tunnel, and rocket/bomb-drop experience. The chart is not a validated solver for an individual rocket fin.

## Appendix equations and definitions

Appendix equations (18) and (19) are transcribed from the original PDF. In source customary units, the screening relation is

\[
\left(\frac{V_f}{a}\right)^2 =
\frac{G_E}{\left[\frac{39.3 A^3}{(t/c)^3(A+2)}\right]
\left(\frac{\lambda+1}{2}\right)\left(\frac{p}{p_0}\right)}.
\]

The chart parameter is

\[
X = \frac{39.3 A^3}{(t/c)^3(A+2)}, \qquad
\text{Figure 3 ordinate}=X\left(\frac{\lambda+1}{2}\right)\left(\frac{p}{p_0}\right).
\]

Definitions as used in TN 4197:

- \(V_f\): flutter velocity; \(a\): speed of sound; \(G_E\): effective shear modulus of an equivalent section.
- \(A=L/c_{0.50}\): exposed aspect ratio of **one wing panel**, with panel span \(L\) and panel chord at midspan \(c_{0.50}\). It is not the whole-vehicle/paired-fin aspect ratio. The derivation evaluates section properties at the three-quarter-span station, relates \(c_{0.75}=c_{0.50}f_2(\lambda)\), and uses \(A=L/c_{0.50}\) in the reduced equation.
- \(t/c\): streamwise section thickness ratio. Equations (15), (18), and (19) print no station subscript on this ratio; Equation (15) explicitly applies to wings of constant thickness ratio. Do not silently assign a station-specific value for a non-constant-thickness fin.
- \(\lambda=c_{tip}/c_{root}\): taper ratio.
- \(p/p_0\): local fluid pressure divided by sea-level standard pressure.
- In this empirical form, the paper assumes air with \(\gamma=1.4\) and \(\epsilon=0.25\). The constant 39.3 is in **psi** (the paper's customary units); therefore \(G_E\) must also be in psi when using 39.3. The speed ratio is dimensionless. In SI, use the equivalent pressure constant \(39.3\,\mathrm{psi}=270.9\,\mathrm{kPa}\) in the denominator and \(G_E\) in Pa; do not combine the printed 39.3 with a Pa modulus.

The factor \((\lambda+1)/2\) is present in Equation (18) in addition to 39.3, and the report separately states that the Figure 3 ordinate is \(X((\lambda+1)/2)(p/p_0)\). Equation (19) defines \(X\) as the first factor alone. The PDF gives the construction of \(G_E\) for an equivalent solid section and a measured fabricated section:

\[
J_s \simeq \frac{ct^3}{6},\qquad
(JG)_{measured}=J_sG_E,\qquad
G_E=\frac{6(JG)_{measured}}{ct^3}.
\]

It gives the untapered uniform beam torsional frequency \(\omega_\alpha=(\pi/2L)\sqrt{JG/I}\), with tapered-beam correction \(f_1\simeq1+1.87(1-\lambda)^{1.6}\), and the approximation \(1/(f_1^2f_2^2)\simeq(\lambda+1)/2\). These approximations and \(\epsilon=0.25\) are part of the empirical simplification, not general identities.

## Validity limits stated by the report

The underlying Theodorsen-Garrick expression was for heavy, high-aspect-ratio wings with low bending-to-torsion frequency ratio. TN 4197 explicitly says extending its modified criterion to low-aspect-ratio, swept and highly tapered wings stretches the basic formula; the authors adjusted parameters for coherence with their assembled data. Figure 3 separates past safe/unsafe observations probabilistically; its text says more detailed analysis or experiment is needed for marginal designs. The report also states that other flutter forms require different criteria.

Especially relevant to a rocket fin, TN 4197 separately describes *missile pitching / wing bending* flutter and reports rocket-vehicle failures appearing to involve those modes. It says critical speed depends on including the proper degrees of freedom; for that mode bending stiffness and fin location relative to body CG matter. Equation 18 is only the bending-torsion screen and does not close that coupled body-fin mode, stall flutter, local panel/skin flutter, joint flexibility, printed anisotropy, temperature-dependent stiffness, gimbal/aft-module compliance, damping, or servo/control interactions.

## Use in WO-03

Equation 18 is suitable as a traceable preliminary comparison/screen if its inputs, units, actual exposed-panel geometry, material stiffness basis and flight pressure/speed envelope are explicitly documented. Do not declare a flutter pass from the equation alone, assume an inaccessible Figure 3 boundary, or treat a nominal material handbook modulus as the effective \(G_E\) of a fabricated/printed fin-root assembly. For this rocket, a defensible closure needs the actual fin and attachment modal properties plus consideration of body pitch/bending coupling and required vibration/modal measurements. This note records a usable primary-source method; it does not establish a flutter margin.
