try:
    from gcloud_crcmod.crcmod import *
    import gcloud_crcmod.predefined
except ImportError:
    # Make this backward compatible
    from crcmod import *
    import predefined
__doc__ = crcmod.__doc__
