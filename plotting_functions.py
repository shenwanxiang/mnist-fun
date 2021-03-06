import numpy as np
from keras_model import *
from additional_functions import *
# import matplotlib  # necessary to save plots remotely; comment out if local
# matplotlib.use('Agg')  # comment out if local
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import pylab
from keras.utils import np_utils
import pandas as pd
from mpl_toolkits.mplot3d import Axes3D

### Model Training Functions###
def train_models_on_noisy_data(characteristic_noise_vals, X_or_y):
    ''' 
    INPUT:  (1) 1D numpy array: if on X, should be the standard deviations of
                the Gaussian noise being added; if on y, should be the 
                percentages of labels to be randomly changed
            (2) string: 'X' or 'y' corresponding to which data to make noisy
    OUTPUT: None, directly at least. All models will be saved to /models    
    This function loads the basic data, then loops through the characteristic
    noise values and trains models on those noisy data. Classwise accuracies 
    can then be calculated from these models. 
    '''
    model_param = set_basic_model_param(0)
    X_train, y_train, X_test, y_test = load_and_format_mnist_data(model_param,
                                            categorical_y=False)
    for cnv in characteristic_noise_vals:
        name_to_append = '{}_{}'.format(X_or_y, cnv)
        model_param = set_basic_model_param(name_to_append)
        if X_or_y == 'X':
            print 'Training models with noise lev of {}'.format(cnv)
            noisy_X_train = add_gaussian_noise(X_train, mean=0, stddev=cnv)
            y_train = np_utils.to_categorical(y_train, model_param['n_classes'])
            y_test = np_utils.to_categorical(y_test, model_param['n_classes'])
            model = compile_model(model_param)
            fit_and_save_model(model, model_param, noisy_X_train, y_train, 
                               X_test, y_test)
        if X_or_y == 'y':
            print 'Training models with {}% random labels'.format(cnv)
            noisy_y_train = add_label_noise(y_train, cnv)
            noisy_y_train = np_utils.to_categorical(noisy_y_train, 
                                                    model_param['n_classes'])
            y_test = np_utils.to_categorical(y_test, model_param['n_classes'])
            model = compile_model(model_param)
            fit_and_save_model(model, model_param, X_train, noisy_y_train, 
                               X_test, y_test)


def train_model_meshgrid(percent_random_labels, batchsizes, dropout_scalars):
    ''' 
    INPUT:  (1) 1D numpy array: fraction of y labels to randomize
            (2) 1D numpy array: size of batches to train models on
            (3) 1D numpy array: the scalars by which to change the 
                built-in dropout values (0.25 and 0.5: see keras_model
                for specifics)
    OUTPUT: None, but all models will be saved to /models

    This function trains models on a mesh of parameters (percent random labels,
    batch sizes, and dropout levels). Model accuracies can then be calculated
    from these models to be plotted in 3 dimensions: see calc_meshgrid_acc.
    '''
    model_param = set_basic_model_param(0)
    X_train, y_train, X_test, y_test = load_and_format_mnist_data(model_param,
                                            categorical_y=False)
    for percent_random in percent_random_labels:
        noisy_y_train = add_label_noise(y_train, percent_random)
        noisy_y_train = np_utils.to_categorical(noisy_y_train, 
                                                model_param['n_classes'])
        y_test = np_utils.to_categorical(y_test, model_param['n_classes'])
        for batchsize in batchsizes:
            for dropout_scalar in dropout_scalars:
                print '''Training model with {} random labels, a batchsize of {}, and a dropout scalar of {}'''.format(percent_random, batchsize, dropout_scalar)
                name_to_append = 'y_{}_{}_{}'.format(percent_random, batchsize,
                                                     dropout_scalar)
                model_param = set_basic_model_param(name_to_append, 
                                dropout_scalar=dropout_scalar,
                                batchsize=batchsize)
                model = compile_model(model_param)
                fit_and_save_model(model, model_param, X_train, noisy_y_train, 
                                   X_test, y_test)

### Accuracy Calculating Functions###
def calc_all_classwise_accs(noise_stddevs):
    '''
    INPUT:  (1) 1D numpy array: The standard deviations of the Gaussian noise 
                being added to the data
    OUTPUT: (1) dictionary of lists: The accuracies over all standard deviations 
                for each digit in MNIST

    This function calculates the classwise accuracies as a function of the
    standard deviation of the Gaussian noise added to the X training data. 
    It isn't set up to handle the noisy y data, as classwise accuracies 
    do not make much sense to calculate when looking at the effect that
    randomizing some percentage of the labels has on the model performance. 
    '''
    model_param = set_basic_model_param(noise_stddevs[0])
    X_train, y_train, X_test, y_test = load_and_format_mnist_data(model_param, 
                                                categorical_y=False)
    unique_classes = np.unique(y_test)
    classwise_accs = {unique_class: [] for unique_class in unique_classes}
    for noise_stddev in noise_stddevs:
        print '''Calculating classwise accs for model characteristic noise value
                of of {}'''.format(x)
        name_to_append = '{}_{}'.format('X', noise_stddev)
        model = load_model('models/KerasBaseModel_v.0.1_{}'.format(name_to_append))
        classwise_accs_to_add = predict_classwise_top_n_acc(model, X_test,
                                                            y_test)
        for elt in classwise_accs_to_add.keys():
            classwise_accs[elt].append(classwise_accs_to_add[elt])
    return classwise_accs


def calc_raw_acc(characteristic_noise_vals, X_or_y):
    ''' 
    INPUT:  (1) 1D numpy array: if on X, should be the standard deviations of
                the Gaussian noise being added; if on y, should be the 
                percentages of labels to be randomly changed
            (2) string: 'X' or 'y' corresponding to which data was made noisy
                before training the models for which we are calculating the acc

    This function calculates the raw accuracy (over all classes) a series of
    models with different characteristic noise values.
    '''
    model_param = set_basic_model_param(0)    
    X_train, y_train, X_test, y_test = load_and_format_mnist_data(model_param, 
                                                categorical_y=False)
    accs = []
    for cnv in characteristic_noise_vals:
        print '''Calculating raw accuracy for models with a characteristic 
                 noise value of {}'''.format(cnv)
        name_to_append = '{}_{}'.format(X_or_y, cnv)
        model = load_model('models/KerasBaseModel_v.0.1_{}'.format(name_to_append))
        y_pred = model.predict_classes(X_test)
        acc_to_add = np.sum(y_pred == y_test) / float(len(y_test))
        accs += [acc_to_add]
    return accs 


def calc_meshgrid_acc(percent_random_labels, batchsizes, dropout_scalars):
    '''
    INPUT:  (1) 1D numpy array: fraction of y labels to randomize
            (2) 1D numpy array: size of batches to train models on
            (3) 1D numpy array: the scalars by which to change the 
                built-in dropout values (0.25 and 0.5: see keras_model
                for specifics)
    OUTPUT: (1) 3D numpy array of accuracies corresponding to the models
                trained on the grid of parameters specified in the input

    This function will calculate all accuracies for the grid of model
    parameters being varied. All models must have been trained and saved
    in /models using train_model_meshgrid before this function can be
    utilized.
    '''
    model_param = set_basic_model_param(0)    
    X_train, y_train, X_test, y_test = load_and_format_mnist_data(model_param, 
                                                categorical_y=False)
    acc_grid = np.zeros((len(percent_random_labels), 
                         len(batchsizes), 
                         len(dropout_scalars)))
    for pr_ind, percent_random in enumerate(percent_random_labels):
        for b_ind, batchsize in enumerate(batchsizes):
            for d_ind, dropout_scalar in enumerate(dropout_scalars):
                print '''Calculating raw accuracy for model with {} random labels, a batchsize of {}, and a dropout scalar of {}'''.format(percent_random, batchsize, dropout_scalar)
                name_to_append = 'y_{}_{}_{}'.format(percent_random, batchsize,
                                                     dropout_scalar)
                model_param = set_basic_model_param(name_to_append, 
                                dropout_scalar=dropout_scalar,
                                batchsize=batchsize)
                model = load_model('models/KerasBaseModel_v.0.1_{}'.format(name_to_append))
                y_pred = model.predict_classes(X_test)
                acc_to_add = np.sum(y_pred == y_test) / float(len(y_test))
                print 'Accuracy is {}\n'.format(acc_to_add)
                acc_grid[pr_ind, b_ind, d_ind] = acc_to_add
    return acc_grid


def calc_meshgrid_time_to_converge(percent_random_labels, batchsizes, dropout_scalars):
    '''
    INPUT:  (1) 1D numpy array: fraction of y labels to randomize
            (2) 1D numpy array: size of batches to train models on
            (3) 1D numpy array: the scalars by which to change the 
                built-in dropout values (0.25 and 0.5: see keras_model
                for specifics)
    OUTPUT: (1) 3D numpy array of the number of epochs it took the model 
                at that point on the grid to converge
    '''
    converge_grid = np.zeros((len(percent_random_labels), 
                              len(batchsizes), 
                              len(dropout_scalars)))
    for pr_ind, percent_random in enumerate(percent_random_labels):
        for b_ind, batchsize in enumerate(batchsizes):
            for d_ind, dropout_scalar in enumerate(dropout_scalars):
                name_to_append = 'y_{}_{}_{}'.format(percent_random, batchsize,
                                                     dropout_scalar)
                filename = 'models/KerasBaseModel_v.0.1_{}.pkl'.format(name_to_append)
                model_history = pickle.load(open(filename, 'rb'))
                n_epochs = len(model_history['acc'])
                converge_grid[pr_ind, b_ind, d_ind] = n_epochs
    return converge_grid


### Plotting Functions ###
def plot_acc_vs_noisy_X(noise_stddevs, classwise_accs, saveas):
    ''' 
    INPUT:  (1) 1D numpy array: The standard deviations of the Gaussian noise 
                being added to the data
            (2) dictionary of lists: The accuracies over all standard deviations 
                for each digit in MNIST (the output of calc_all_classwise_accs)
            (3) string: the name to save the plot
    OUTPUT: None. However, the plot will be saved at the specified location.

    Classwise accuracies will be plotted vs. the standard deviation of Gaussian
    noise added to the X training data. A rolling mean is applied to make the 
    plot readable; nans created by the rolling mean are filled with original
    values for completeness.
    '''
    unique_classes = sorted(classwise_accs.keys())
    color_inds = np.linspace(0, 1, len(unique_classes))
    for color_ind, unique_class in zip(color_inds, unique_classes):
        rolling_mean = pd.rolling_mean(np.array(classwise_accs[unique_class]),
                                       window=3, center=False)
        null_ind_from_rolling = np.where(pd.isnull(rolling_mean))[0]
        orig_vals_to_fill_nulls = np.array(classwise_accs[unique_class])[null_ind_from_rolling]
        rolling_mean[null_ind_from_rolling] = orig_vals_to_fill_nulls
        plt.plot(noise_stddevs, rolling_mean, 
                 color=plt.cm.jet(color_ind), label=str(unique_class))
    plt.xlabel('Standard Deviation of Gaussian Noise Added to Training Data')
    
### Plotting Functions ###
def plot_acc_vs_noisy_X(noise_stddevs, classwise_accs, saveas):
    ''' 
    INPUT:  (1) 1D numpy array: The standard deviations of the Gaussian noise 
                being added to the data
            (2) dictionary of lists: The accuracies over all standard deviations 
                for each digit in MNIST (the output of calc_all_classwise_accs)
            (3) string: the name to save the plot
    OUTPUT: None. However, the plot will be saved at the specified location.

    Classwise accuracies will be plotted vs. the standard deviation of Gaussian
    noise added to the X training data. A rolling mean is applied to make the 
    plot readable; nans created by the rolling mean are filled with original
    values for completeness.
    '''
    unique_classes = sorted(classwise_accs.keys())
    color_inds = np.linspace(0, 1, len(unique_classes))
    for color_ind, unique_class in zip(color_inds, unique_classes):
        rolling_mean = pd.rolling_mean(np.array(classwise_accs[unique_class]),
                                       window=3, center=False)
        null_ind_from_rolling = np.where(pd.isnull(rolling_mean))[0]
        orig_vals_to_fill_nulls = np.array(classwise_accs[unique_class])[null_ind_from_rolling]
        rolling_mean[null_ind_from_rolling] = orig_vals_to_fill_nulls
        plt.plot(noise_stddevs, rolling_mean, 
                 color=plt.cm.jet(color_ind), label=str(unique_class))
    plt.xlabel('Standard Deviation of Gaussian Noise Added to Training Data')
    plt.ylabel('Accuracy')
    plt.legend(loc=3)
    plt.savefig('{}.png'.format(saveas), dpi=200)


def plot_acc_vs_noisy_y(percent_random_labels, accs, saveas):
    '''
    INPUT:  (1) 1D numpy array: The fraction of training labels randomized
            (2) list: The accuracies for each model (the output of 
                calc_raw_acc with 'y')
            (3) string: the name to save the plot
    OUTPUT: None. However, the plot will be saved at the specified location.
    '''
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot(percent_random_labels, accs, label='Model Accuracy on Test Set')
    ax.set_xlabel('Percent of Training Labels Randomized')
    ax.set_ylabel('Accuracy')
    x_tick_vals = ax.get_xticks()
    ax.set_xticklabels(['{:2.1f}%'.format(x * 100) for x in x_tick_vals])
    ax.set_xlim(0, .33)
    ax.set_ylim(0, 1)
    ax.axhline(.1, ls=':', color='k', label='Naive Guessing')
    ax.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3,
               ncol=2, mode="expand", borderaxespad=0.)
    fig.savefig('{}.png'.format(saveas), dpi=200)


def plot_acc_vs_noisy_y_surface(percent_random_labels, batchsizes, 
                                dropout_scalars, acc_grid, saveas=None):
    ''' 
    INPUT:  (1) 1D numpy array: fraction of y labels to randomize
            (2) 1D numpy array: size of batches to train models on
            (3) 1D numpy array: the scalars by which to change the 
                built-in dropout values (0.25 and 0.5: see keras_model
                for specifics)
            (4) 3D numpy array of accuracies corresponding to the models
                trained on the grid of parameters specified in the input
            (5) string, optional: the filename to save the plot as
    '''
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    color_inds = np.linspace(0, 1, len(dropout_scalars))
    x = percent_random_labels
    y = np.log2(batchsizes)[2:]
    xxyy = np.meshgrid(x, y)
    xx = xxyy[0]
    yy = xxyy[1]
    acc_grid_layers = [acc_grid[:, 2:, 0], acc_grid[:, 2:, 1]]
    dropout_labels = ['No Dropout', 'With Dropout']
    for acc_grid, color_ind, dropout_label in zip(acc_grid_layers, 
                                                 color_inds,
                                                 dropout_labels):
        z = acc_grid
        c = plt.cm.winter(color_ind)
        ax.plot_wireframe(xx, yy, z.T, color=c, label=dropout_label)
    naive_model = 0.1 * np.ones((len(y), len(x))) 
    ax.plot_wireframe(xx, yy, naive_model, color='k', label='Naive Model')
    ax.set_xlabel('Percent of Training Labels Randomized')
    x_tick_vals = ax.get_xticks()
    ax.set_xticklabels(['{:2.0f}%'.format(x_val * 100) for x_val in x_tick_vals])
    ax.set_ylabel('log2(Batch Size)')
    ax.set_zlabel('Accuracy')
    plt.legend()
    if saveas is not None:
        plt.savefig('{}.png'.format(saveas))
    else:
        plt.show()


### Visualizing Noisy X Functions###
def show_1_noisy_X_example(noise_stddevs, X_train, ind_to_display=0):
    ''' 
    INPUT:  (1) 1D numpy array: standard deviations of the Gaussian noise to add
                to an example image from the X training data. Note that the image
                data has not yet been scaled from 0 to 1, but still has values
                between 0 and 255
            (2) 4D numpy array: X training data
            (3) integer: the index from X_train to display with noise over it
    OUTPUT: None, but the plot will show to screen
    
    This function displays one image (specified by ind_to_display) 
    with increasing levels of Gaussian noise on top of it.
    '''
    fig = plt.figure(figsize=(8, 1))
    outer_grid = gridspec.GridSpec(1, 13, wspace=0.0, hspace=0.0)
    pylab.xticks([])
    pylab.yticks([])
    for i, noise_stddev in zip(range(13), noise_stddevs[::8]):
        X_train_noisy = add_gaussian_noise(X_train, 0, noise_stddev)
        ax = plt.Subplot(fig, outer_grid[i])
        ax.imshow(X_train_noisy[ind_to_display].reshape((28,28)), cmap=plt.cm.Greys)
        ax.set_xticks([])
        ax.set_yticks([])
        fig.add_subplot(ax)
    plt.show()


def show_all_noisy_X_example(noise_stddevs, X_train, y_train):
    ''' 
    INPUT:  (1) 1D numpy array: standard deviations of the Gaussian noise to add
                to example images from the X training data. Note that the image
                data has not yet been scaled from 0 to 1, but still has values
                between 0 and 255. Hardcoded to work with the len of this array
                at 97 (the total number of models trained) such that taking 
                every 8th element results in 13 examples (which is the hardcoded
                number of columns for this function)
            (2) 4D numpy array: X training data
            (3) 1D numpy array: y training data: the first instance of each digit
                will be taken from these labels so that an example of each
                digit can be shown
    OUTPUT: None, but the plot will show to screen
    
    This function displays an example of each digit from the X training data
    with increasing levels of Gaussian noise on top of it. The function is 
    hardcoded such that 13 examples of increasing noise will be shown. 
    '''
    fig = plt.figure(figsize=(10,10))
    outer_grid = gridspec.GridSpec(10, 13, wspace=0.0, hspace=0.0)
    pylab.xticks([])
    pylab.yticks([])
    first_ind_of_each_num = {i: np.where(y_train == i)[0][0] for i in range(10)}
    for col_ind, noise_stddev in zip(range(13), noise_stddevs[::8]):
        X_train_noisy = add_gaussian_noise(X_train, 0, noise_stddev)
        for row_ind in range(10):
            ind_to_plot = col_ind + row_ind * 13
            ax = plt.Subplot(fig, outer_grid[ind_to_plot])
            first_ind_of_this_num = first_ind_of_each_num[row_ind]
            ax.imshow(X_train_noisy[first_ind_of_this_num].reshape((28,28)), 
                      cmap=plt.cm.Greys)
            ax.set_xticks([])
            ax.set_yticks([])
            fig.add_subplot(ax)
            if ax.is_last_row():
                ax.set_xlabel('{}'.format(noise_stddev))
    plt.show()


### Master Functions###
def load_data_and_show_noisy_X():
    ''' 
    INPUT:  None
    OUTPUT: None, but the plot from show_all_noisy_X_example will show to screen
    
    This function loads the data and utilizes show_all_noisy_X_example to
    give an example of what the training data look like with increasing levels
    of Gaussian noise. 
    '''
    model_param = set_basic_model_param(0)
    noise_stddevs = np.linspace(0, 192, 97)
    X_train, y_train, X_test, y_test = load_and_format_mnist_data(model_param)
    show_all_noisy_X_example(noise_stddevs, X_train, y_train)


def load_meshgrid_param():
    ''' 
    INPUT:  None
    OUTPUT: (1) 1D numpy array: fraction of y labels to randomize
            (2) 1D numpy array: size of batches to train models on
            (3) 1D numpy array: the scalars by which to change the 
                built-in dropout values (0.25 and 0.5: see keras_model
                for specifics)

    This function sets and returns the required param for the meshgrid,
    and is utilized in save_accuracy_meshgrid and plot_accuracy_meshgrid
    '''
    percent_random_labels = np.linspace(0, 0.8, 17)
    batchsizes = 2**np.arange(3, 11)
    dropout_scalars = np.array([0, 1])
    return percent_random_labels, batchsizes, dropout_scalars


def save_accuracy_meshgrid(acc_grid_filename):
    ''' 
    INPUT:  (1) string: the filename to save the pickled 3D numpy array of
                accuracies to
    OUTPUT: None, but the accuracy grid will be saved
    
    The grid parameters (percent random labels, batchsizes, and dropout 
    scalars) are set in this function. The full model swarm is trained,
    then the full accuracy grid is calculated. The accuracy grid will be
    saved as a pickled numpy array.
    '''
    percent_random_labels, batchsizes, dropout_scalars = load_meshgrid_param()
    train_model_meshgrid(percent_random_labels, batchsizes, dropout_scalars)
    acc_grid = calc_meshgrid_acc(percent_random_labels, batchsizes, 
                                    dropout_scalars)
    acc_grid.dump('{}.pkl'.format(acc_grid_filename))


def save_time_to_converge_meshgrid(converge_grid_filename):
    ''' 
    INPUT:  (1) string: the filename to save the pickled 3D numpy array of
                number of epochs it took the model to converge to
    OUTPUT: None, but the grid will be saved
    
    The grid parameters (percent random labels, batchsizes, and dropout 
    scalars) are set in this function. Models must have already been trained. 
    The grid will be saved as a pickled numpy array.
    '''
    percent_random_labels, batchsizes, dropout_scalars = load_meshgrid_param()
    converge_grid = calc_meshgrid_time_to_converge(percent_random_labels, batchsizes, 
                                    dropout_scalars)
    converge_grid.dump('{}.pkl'.format(converge_grid_filename))


def plot_accuracy_meshgrid(acc_grid_filename, saveas=None):
    ''' 
    INPUT:  (1) string: the filename to read the pickled 3D numpy array of 
                accuracies from
            (2) string: the filename to save the plot to. If 'None' the 
                plot will show to screen
    OUTPUT: None, but the plot will show or be saved depending on 'saveas'
    '''
    percent_random_labels, batchsizes, dropout_scalars = load_meshgrid_param()
    acc_grid = np.load(acc_grid_filename)
    plot_acc_vs_noisy_y_surface(percent_random_labels, batchsizes, 
                                dropout_scalars, acc_grid,
                                saveas=saveas)
