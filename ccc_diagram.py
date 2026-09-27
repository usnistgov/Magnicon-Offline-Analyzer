"""Draws the CCC bridge circuit with schemdraw"""
import schemdraw
import schemdraw.elements as elm

def _value(value, unit: str = '') -> str:
    """Formats a value for the diagram, empty when there is no value to show"""
    return '' if value in ('', None) else f'{value} {unit}'.strip()

def _stacked(symbol: str, value: str) -> str:
    """Symbol with its value on the line below"""
    return symbol + ('\n' + value if value else '')

def draw_ccc_diagram(ax, R1='', R2='', N1='', N2='', I1='', I2='', BVD='', Na='', RH='', RL='', Ia='') -> None:
    """Draws the CCC bridge on a matplotlib axes, annotated with the values of a measurement

    Parameters
    ----------
    ax : matplotlib Axes to draw on
    R1, R2 : nominal values of the resistors [Ohm]
    N1, N2, Na : turns of the primary, secondary and auxiliary windings
    I1, I2, Ia : primary, secondary and auxiliary currents [A]
    BVD : bridge voltage difference [V]
    RH, RL : settings of the compensation network resistors
    Values left empty are not shown.

    Returns
    -------
    None
    """
    red, blue = 'red', 'blue'
    xI1, xR1, xR2, xI2 = 0, 4, 10, 14                       # columns: I1, R1/N1/NA, R2/N2, I2
    yTop, yR, yU, yN, yF, yBot = 13, 11, 8, 5, 2.5, 0       # rows: top, R tops, R bottoms, windings, feedback, bottom
    with schemdraw.Drawing(canvas=ax, show=False) as d:
        d.config(fontsize=13, lw=1.5, font='Times New Roman')
        # primary: I1 -> R1 -> N1, then RL in parallel with NA + RH back to I1
        elm.Line(color=red).at((xI1, yBot)).toy(yN)
        elm.Dot(color=red)
        elm.SourceI(color=red).up().toy(yU).label(_stacked('$I_1$', _value(I1, 'A')), loc='top')
        elm.Line(color=red).toy(yTop)
        elm.Line(color=red).tox(xR1)
        elm.Line(color=red).toy(yR)
        elm.Dot(color=red)
        elm.Resistor(color=red).down().toy(yU).label('$R_1$', loc='bottom').label(_value(R1, '$\\Omega$'), loc='top')
        elm.Dot(color=red)
        elm.Inductor2(color=blue, loops=4).down().toy(yN).label('$N_1$', loc='bottom').label(_value(N1), loc='top')
        elm.Dot(color=blue)
        elm.ResistorVar(color=red).at((xI1, yN)).right().tox(xR1).label('$R_L$', loc='top').label(_value(RL), loc='bottom')
        elm.Inductor2(color=blue, loops=4).at((xR1, yN)).down().toy(yF - 0.5).label('$N_A$', loc='top').label(_value(Na), loc='bottom')
        elm.Line(color=blue).toy(yBot)
        elm.CurrentLabelInline(direction='in', color=blue).at(d.elements[-1]).label('$I_A$ ' + _value(Ia, 'A'), loc='bottom')
        elm.ResistorVar(color=red).at((xI1, yBot)).right().tox(xR1).label('$R_H$', loc='top').label(_value(RH), loc='bottom')
        # secondary: I2 -> R2 -> N2 and back to I2
        elm.Line(color=red).at((xR1, yR)).tox(xR2)
        elm.Dot(color=red)
        elm.Resistor(color=red).down().toy(yU).label('$R_2$', loc='top').label(_value(R2, '$\\Omega$'), loc='bottom')
        elm.Dot(color=red)
        elm.Inductor2(color=blue, loops=4).down().toy(yN).label('$N_2$', loc='top').label(_value(N2), loc='bottom')
        elm.Dot(color=blue)
        elm.Line(color=blue).toy(yBot)
        elm.Line(color=blue).tox(xI2)
        elm.Line(color=red).toy(yF)
        elm.Dot(color=red)
        elm.Line(color=red).toy(yN)
        elm.SourceI(color=red).up().toy(yU).label(_stacked('$I_2$', _value(I2, 'A')), loc='bottom')
        elm.Line(color=red).toy(yTop)
        elm.Line(color=red).tox(xR2)
        elm.Line(color=red).toy(yR)
        # bridge voltage difference between the lower ends of R1 and R2, grounded at R2
        elm.MeterV(color=red).at((xR1, yU)).right().tox(xR2).label('$\\Delta U$', loc='bottom').label(_value(BVD, 'V'), loc='top')
        elm.Line(color=red).at((xR2, yU)).right(1.2)
        elm.Ground(color=red).theta(90)
        # SQUID, coupled to the windings and feeding back into the secondary
        r = 0.9 # radius of the SQUID symbol
        squid = elm.Source(color=blue).scale(2*r).at(((xR1 + xR2)/2 - r, yN)).right().length(2*r).label('$\\phi$', loc='center')
        elm.Line(color=blue, ls=':').at((xR1, yN)).to(squid.start)
        elm.Line(color=blue, ls=':').at(squid.end).to((xR2, yN))
        elm.Arrow(color=red, ls='--').at(((xR1 + xR2)/2, yN - r)).down().toy(yF).label('$i_f$', loc='bottom')
        elm.Line(color=red, ls='--').tox(xI2)
    d.draw(show=False)
    # leave room for the labels outside the circuit, keeping circles round whatever the size of the axes
    ax.set_xlim(xI1 - 2.6, xI2 + 2.6)
    ax.set_ylim(yBot - 1.1, yTop + 0.4)
    ax.set_aspect('equal')
    ax.set_axis_off()
