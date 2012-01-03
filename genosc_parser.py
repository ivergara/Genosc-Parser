#!/usr/bin/env python
# -*- coding: utf-8 -*-
#Author: Ignacio Vergara Kausel

#===============================================================================
# This work is licensed under the Creative Commons
# Attribution-NonCommercial-ShareAlike 3.0 Unported License.
# To view a copy of this license, visit
# http://creativecommons.org/licenses/by-nc-sa/3.0/
# or send a letter to Creative Commons, 444 Castro Street,
# Suite 900, Mountain View, California, 94041, USA.
#===============================================================================

import csv, sys, os, argparse

from math import pi

PERM = 8.85418781762e-12 # Vacuum Permitivity in F/m
HBAR = 6.58211928e-16 # Planck's Constant in eV*s


class Sample():
    """Parses a collection of (WVase) Genosc models and saves each oscillator in the model in an independent file for the whole set of models."""

    def __init__(self, **kwargs):
        self.models = None # Contains all the models loaded
        self.kwargs = kwargs # All the arguments

    def loadModels(self):
        """Loads all the files present in the path given at construction time
        of the Sample instance."""
        #don't know if this previous lookup gives efficiency or legibility
        join = os.path.join
        listdir = os.listdir
        path = self.kwargs['path']
        self.models = [GenoscModel(join(path, file)) for file in listdir(path)]

    def exportOscillators(self):
        """Saves one file per oscillator containing all temperatures."""
        for oscillator in xrange(self.kwargs['oscillators']):
            _string = '_'.join((str(oscillator), self.kwargs['label'],self.kwargs['output']))
            with open(_string, 'wb') as f:
                writer = csv.writer(f, delimiter='\t') # Cols separated by <tab>
                writer.writerow([self.kwargs['description']])
                writer.writerow(['T', 'Energy', 'Amplitude', 'Width']) #Header
                for model in self.models: # Writes the data into the table
                    writer.writerow([self.models[0].temperature,
                                     model.oscillators[oscillator].energy,
                                     model.oscillators[oscillator].amplitude,
                                     model.oscillators[oscillator].width,
                                     model.oscillators[oscillator].sw])


class GenoscModel():
    """A particular Genosc model representation class.
    Imports a Genosc model file with the following name convention:
        temp_axis_anythingelse.whatever"""

    def __init__(self, filename):
        self.oscillators = []
        #Takes the route, picks the filename and extracts the temperature
        self._params = filename.split('\\')[-1].split('_')
        self.temperature = self._params[0][:-1]
        self.axis = self._params[1] #fix issue with extension

        with open(filename, 'rb') as f:
            reader = csv.reader(f)
            try:
                for i in xrange(5): #getting rid of the header
                    reader.next()
                for row in reader:
                    row = row[0].split()
                    if row[1] == '0':
                        self.oscillators.append(LorentzOsc(row[3], row[4], row[5]))
                    elif row[1] == '2':
                        self.oscillators.append(GaussOsc(row[3], row[4], row[5]))
                    elif row[1] == '6':
                        self.oscillators.append(DrudeOsc(row[3], row[4]))
            except csv.Error, e:
                sys.exit('file %s, line %d: %s' % (filename, reader.line_num, e))


class Oscillator(object):
    """Base class of an genosc oscilator."""

    def __init__(self, amplitude, energy, width):
        self.sw = 0
        self.plasmafrequency = 0
        self.amplitude = float(amplitude)
        self.energy = float(energy)
        self.width = float(width)

    def spectralWeight(self):
        """Calculates the area of the oscillator given its
           parameters."""
        pass

    def plasmaFrequency(self):
        """Calculates the square of plasma frequency in eV^2 of
        the oscillator given its parameters."""
        pass

class DrudeOsc(Oscillator):
    """Drude oscillator."""
    def __init__(self, amplitude, width):
        super(DrudeOsc, self).__init__(amplitude, 0, width)
        self.spectralWeight()

    def spectralWeight(self):
        self.sw = pi/2*PERM/HBAR**2*self.amplitude*self.width

    def plasmaFrequency(self):
        self.plasmafrequency = self.amplitude*self.width

class LorentzOsc(Oscillator):
    """Lorentz oscillator."""
    def __init__(self, amplitude, energy, width):
        super(LorentzOsc, self).__init__(amplitude, energy, width)
        self.spectralWeight()

    def spectralWeight(self):
        self.sw = (self.amplitude*self.energy*self.width)

    def plasmaFrequency(self):
        self.plasmafrequency = self.amplitude*self.width*self.energy

class GaussOsc(Oscillator):
    """Gauss oscillator."""
    def __init__(self, amplitude, energy, width):
        super(GaussOsc, self).__init__(amplitude, energy, width)
        self.spectralWeight()

    def spectralWeight(self):
        self.sw = (self.amplitude*self.energy*self.width)

    def plasmaFrequency(self):
        raise NotImplementedError

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
             epilog = "One use example.",
             description = 'Extract data from a set of WVase Genosc models.')
    parser.add_argument('path', help='path to the folder containing the models.')
    parser.add_argument('-l', '--label', help='Label. e.g. orientation and axis i.e a-ac.')
    parser.add_argument('-o', '--output', help='Name of the output file.')
    parser.add_argument('-d', '--description', help='Description line.')
    parser.add_argument('-s', '--oscillators', type=int, help='Number of oscillators in the model.')
    args = parser.parse_args()

    sample = Sample(**vars(args))
    sample.loadModels()
    sample.exportOscillators()