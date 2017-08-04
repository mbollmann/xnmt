import dynet as dy
from batcher import *
from serializer import *
from expression_sequence import ExpressionSequence
import model_globals

class Attender(object):
  '''
  A template class for functions implementing attention.
  '''

  def __init__(self, input_dim):
    """
    :param input_dim: every attender needs an input_dim
    """
    pass

  def start_sent(self, sent):
    raise NotImplementedError('start_sent must be implemented for:', self.__class__.__name__)

  def calc_attention(self, state, normalized=True):
    raise NotImplementedError('calc_attention must be implemented for:', self.__class__.__name__)

class TranslatorAttender(Attender):
  def calc_context(self, state):
    pass

class StandardAttender(TranslatorAttender, Serializable):
  '''
  Implements the attention model of Bahdanau et. al (2014)
  '''

  yaml_tag = u'!StandardAttender'

  def __init__(self, input_dim=None, state_dim=None, hidden_dim=None):
    input_dim = input_dim or model_globals.get("default_layer_dim")
    state_dim = state_dim or model_globals.get("default_layer_dim")
    hidden_dim = hidden_dim or model_globals.get("default_layer_dim")
    self.input_dim = input_dim
    self.state_dim = state_dim
    self.hidden_dim = hidden_dim
    param_collection = model_globals.dynet_param_collection.param_col
    self.pW = param_collection.add_parameters((hidden_dim, input_dim))
    self.pV = param_collection.add_parameters((hidden_dim, state_dim))
    self.pb = param_collection.add_parameters(hidden_dim)
    self.pU = param_collection.add_parameters((1, hidden_dim))
    self.curr_sent = None

  def start_sent(self, sent):
    self.attention_vecs = []
    self.curr_sent = sent
    I = self.curr_sent
    if type(I) == ExpressionSequence:
      I = I.as_tensor()
    seq_len = I.dim()[0][1]
    W = dy.parameter(self.pW)
    b = dy.parameter(self.pb)
    self.WI = dy.affine_transform([b, W, I])
    if seq_len == 1:
      self.WI = dy.reshape(self.WI, (self.WI.dim()[0][0],1), batch_size=self.WI.dim()[1])

  def calc_attention(self, state, normalized=True):
    V = dy.parameter(self.pV)
    U = dy.parameter(self.pU)

    h = dy.tanh(dy.colwise_add(self.WI, V * state))
    scores = dy.transpose(U * h)
    if normalized:
      scores = dy.softmax(scores)
    self.attention_vecs.append(scores)
    return scores

  def calc_context(self, state):
    attention = self.calc_attention(state)
    I = self.curr_sent.as_tensor()
    return I * attention

